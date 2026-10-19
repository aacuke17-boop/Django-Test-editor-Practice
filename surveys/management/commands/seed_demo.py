import random
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from accounts.models import ANONYMOUS_EMAIL, User
from surveys.demo_data import (
    AUTHOR_SURVEYS,
    AUTHOR_TESTS,
    DEMO_TITLES,
    GHOST_SURVEYS,
    GHOST_TESTS,
)
from surveys.models import (
    Access,
    AnswerOption,
    Attempt,
    Question,
    Questionnaire,
    UserAnswer,
)
from surveys.scoring import calculate_attempt_score

DEMO_PASSWORD = "Demo-pass-123"
ADMIN_EMAIL = "demo-admin@example.com"
ADMIN_PASSWORD = "Admin-pass-123"
GHOST_EMAIL = "ghost@example.com"
USER_EMAILS = [f"user{number}@example.com" for number in range(1, 5)]
DEMO_EMAILS = USER_EMAILS + [ADMIN_EMAIL, GHOST_EMAIL]

PROFILES = {
    "strong": {"perfect": 8, "partial": 1, "mixed": 1},
    "average": {"perfect": 4, "partial": 3, "mixed": 2, "wrong": 1},
    "weak": {"perfect": 1, "partial": 2, "mixed": 2, "wrong": 4, "skip": 1},
    "random": {"perfect": 2, "partial": 2, "mixed": 2, "wrong": 2, "all": 1, "skip": 1},
}


def create_material(author, spec, is_test):
    form = Questionnaire.objects.create(
        creator=author,
        title=spec["title"],
        description=spec["description"],
        is_test=is_test,
        restricted_access=spec["restricted"],
    )
    for position, item in enumerate(spec["questions"], start=1):
        question = Question.objects.create(
            form=form,
            question_text=item["text"],
            points=item["points"] if is_test else 0,
            position=position,
        )
        for option_position, (text, correct) in enumerate(item["options"], start=1):
            AnswerOption.objects.create(
                question=question,
                option_text=text,
                is_correct=correct and is_test,
                position=option_position,
            )
    return form


def pick_test_options(strategy, options):
    correct = [option for option in options if option.is_correct]
    wrong = [option for option in options if not option.is_correct]
    if strategy == "perfect":
        return correct
    if strategy == "partial":
        return correct[: max(1, len(correct) // 2)]
    if strategy == "mixed":
        return correct[:1] + wrong[:1]
    if strategy == "wrong":
        return wrong[:1]
    if strategy == "all":
        return correct + wrong
    return []


def pick_survey_options(rng, options):
    count = rng.choices([0, 1, 2], weights=[1, 7, 2])[0]
    return rng.sample(options, min(count, len(options)))


def create_attempt(rng, form, user, profile):
    questions = list(form.questions.prefetch_related("options"))
    now = timezone.now()
    started = now - timedelta(
        days=rng.randint(0, 29),
        hours=rng.randint(0, 23),
        minutes=rng.randint(0, 59),
    )
    completed = started + timedelta(minutes=rng.randint(1, 25), seconds=rng.randint(0, 59))
    attempt = Attempt.objects.create(
        form=form,
        user=user,
        started_at=started,
        completed_at=completed,
        status=Attempt.STATUS_COMPLETED,
    )

    weights = PROFILES[profile]
    answers = []
    for question in questions:
        options = list(question.options.all())
        if form.is_test:
            strategy = rng.choices(list(weights), weights=list(weights.values()))[0]
            chosen = pick_test_options(strategy, options)
        else:
            chosen = pick_survey_options(rng, options)
        for option in chosen:
            answers.append(UserAnswer(attempt=attempt, question=question, option=option))
    UserAnswer.objects.bulk_create(answers)

    attempt.score = calculate_attempt_score(attempt)
    attempt.save(update_fields=["score"])
    return attempt


class Command(BaseCommand):
    help = "Creates demo users, materials and attempts."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete previously created demo data and create it again.",
        )

    def handle(self, *args, **options):
        if User.objects.filter(email=USER_EMAILS[0]).exists() and not options["reset"]:
            self.stdout.write(
                self.style.WARNING("Demo data already exists. Run with --reset to recreate it.")
            )
            return
        try:
            anonymous = User.objects.get(email=ANONYMOUS_EMAIL)
        except User.DoesNotExist:
            raise CommandError("The Anonymous service user is missing. Run schema.sql first.")

        with transaction.atomic():
            if options["reset"]:
                Questionnaire.objects.filter(title__in=DEMO_TITLES).delete()
                User.objects.filter(email__in=DEMO_EMAILS).delete()
            attempts_count = self.seed(anonymous)

        self.stdout.write(self.style.SUCCESS("Demo data created."))
        self.stdout.write(f"Completed attempts: {attempts_count}")
        self.stdout.write(f"Users user1..user4: password {DEMO_PASSWORD}")
        self.stdout.write(f"Django admin: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")

    def seed(self, anonymous):
        rng = random.Random(2026)
        users = {
            number: User.objects.create_user(
                email=f"user{number}@example.com",
                username=f"user{number}",
                password=DEMO_PASSWORD,
            )
            for number in range(1, 5)
        }
        ghost = User.objects.create_user(
            email=GHOST_EMAIL, username="ghost", password=DEMO_PASSWORD
        )
        User.objects.create_superuser(
            email=ADMIN_EMAIL, username="demo-admin", password=ADMIN_PASSWORD
        )

        profile_names = list(PROFILES)
        completed = 0
        counter = 0

        def run_attempts(form, participants):
            nonlocal completed, counter
            for user in participants:
                profile = profile_names[counter % len(profile_names)]
                counter += 1
                create_attempt(rng, form, user, profile)
                completed += 1

        public_participants = [users[1], users[2], users[3], users[4], ghost, anonymous]
        private_participants = [users[1], users[2], users[1], users[2]]
        ghost_participants = [users[1], users[2], users[3], users[4], anonymous]

        first_public_test = None
        for specs, is_test in ((AUTHOR_TESTS, True), (AUTHOR_SURVEYS, False)):
            for spec in specs:
                form = create_material(users[1], spec, is_test)
                if spec["restricted"]:
                    Access.objects.create(form=form, user=users[2])
                    run_attempts(form, private_participants)
                else:
                    run_attempts(form, public_participants)
                    if is_test and first_public_test is None:
                        first_public_test = form

        for specs, is_test in ((GHOST_TESTS, True), (GHOST_SURVEYS, False)):
            for spec in specs:
                form = create_material(ghost, spec, is_test)
                run_attempts(form, ghost_participants)

        # An unfinished attempt: it must not appear in any statistics
        Attempt.objects.create(
            form=first_public_test,
            user=users[4],
            started_at=timezone.now() - timedelta(hours=1),
        )

        ghost.delete()
        return completed