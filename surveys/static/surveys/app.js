(function () {
    "use strict";

    function initEditor() {
        var list = document.getElementById("questions-list");
        var addButton = document.getElementById("add-question");
        var template = document.getElementById("question-template");

        function renumber() {
            list.querySelectorAll(".question-block").forEach(function (block, i) {
                block.querySelector(".question-number").textContent = String(i + 1);
            });
        }

        function nextIndex() {
            var max = 0;
            list.querySelectorAll('input[name="question_index"]').forEach(function (input) {
                var value = parseInt(input.value, 10);
                if (value > max) {
                    max = value;
                }
            });
            return max + 1;
        }

        addButton.addEventListener("click", function () {
            var html = template.innerHTML.replaceAll("__index__", String(nextIndex()));
            list.insertAdjacentHTML("beforeend", html);
            renumber();
        });

        list.addEventListener("click", function (event) {
            if (event.target.classList.contains("remove-question")) {
                var block = event.target.closest(".question-block");
                if (block) {
                    block.remove();
                    renumber();
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