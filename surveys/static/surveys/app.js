(function () {
    "use strict";

    function initEditor() {
        var list = document.getElementById("questions-list");
        var addQuestionButton = document.getElementById("add-question");
        var questionTemplate = document.getElementById("question-template");
        var optionTemplate = document.getElementById("option-template");

        function renumber() {
            list.querySelectorAll(".question-block").forEach(function (block, i) {
                block.querySelector(".question-number").textContent = String(i + 1);
            });
        }

        function nextIndex(container, selector) {
            var max = 0;
            container.querySelectorAll(selector).forEach(function (input) {
                var value = parseInt(input.value, 10);
                if (value > max) {
                    max = value;
                }
            });
            return max + 1;
        }

        addQuestionButton.addEventListener("click", function () {
            var index = nextIndex(list, 'input[name="question_index"]');
            var html = questionTemplate.innerHTML.replaceAll("__index__", String(index));
            list.insertAdjacentHTML("beforeend", html);
            renumber();
        });

        list.addEventListener("click", function (event) {
            var target = event.target;
            var block = target.closest(".question-block");
            if (!block) {
                return;
            }

            if (target.classList.contains("remove-question")) {
                block.remove();
                renumber();
            } else if (target.classList.contains("add-option")) {
                var optionsList = block.querySelector(".options-list");
                var questionIndex = block.querySelector('input[name="question_index"]').value;
                var optionIndex = nextIndex(optionsList, 'input[type="hidden"]');
                var html = optionTemplate.innerHTML
                    .replaceAll("__qindex__", questionIndex)
                    .replaceAll("__oindex__", String(optionIndex));
                optionsList.insertAdjacentHTML("beforeend", html);
            } else if (target.classList.contains("remove-option")) {
                var optionBlock = target.closest(".option-block");
                if (optionBlock) {
                    optionBlock.remove();
                }
            }
        });

        renumber();
    }

    document.addEventListener("DOMContentLoaded", function () {
        if (document.getElementById("questions-list")) {
            initEditor();
        }
    });
})();