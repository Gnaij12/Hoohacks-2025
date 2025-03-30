(function () {
    let json = $("#data_store").data("json");

    let question_element = $("#question");
    let card_elements = $("[id^=card_]");
    let owl_left_element = $("#owl_left");
    let owl_right_element = $("#owl_right");
    let marsh_left_element = $("#marsh_left");
    let marsh_right_element = $("#marsh_right");

    let num_correct = 0;
    let question_set;
    let question;
    let answer;
    let wrong_questions = [];

    function set_next_question_set() {
        let keys = Object.keys(json);
        let random_keys = [];

        if (Object.keys(json).length < 4) {
            return;
        }

        while (random_keys.length != 4) {
            let random_key = keys[(keys.length * Math.random()) << 0];
            if (!random_keys.includes(random_key)) {
                random_keys.push(random_key);
            }
        }

        question_set = random_keys;
        question = question_set[0];
        answer = json[question];
        question_set = question_set
            .map((x) => ({ x, key: Math.random() }))
            .sort((a, b) => a.key - b.key)
            .map(({ x }) => x);

        for (let i = 0; i < 4; ++i) {
            card_elements[i].innerHTML = json[question_set[i]];
        }
        question_element[0].innerHTML = `Which definition matches the term "${question}" ?`;
    }

    function toggle_owl_visibility(is_left) {
        if (is_left) {
            owl_left_element.css("display", (owl_left_element.css("display") === "none") ? "block" : "none");
        } else {
            owl_right_element.css("display", (owl_right_element.css("display") === "none") ? "block" : "none");
        }
    }

    $("#toggleOwlLeft").on("click", function () {
        toggle_owl_visibility(true);
    });


    $("#toggleOwlRight").on("click", function () {
        toggle_owl_visibility(false); 
    });

    function update_marsh_animation(is_left, success) {
        if (is_left) {
            marsh_left_element.find("img")[0].src = success ? "/static/img/marsh_toast_L.gif" : "static/img/marsh_burn_L.gif";
        } else {
            marsh_right_element.find("img")[0].src = success ? "/static/img/marsh_toast_L.gif" : "static/img/marsh_burn_L.gif";
        }
    }

    function reset_marsh(is_left) {
        if (is_left) {
            marsh_left_element.find("img")[0].src = "/static/img/marsh_L.png";
        } else {
            marsh_right_element.find("img")[0].src = "/static/img/marsh_R.png";
        }
    }

    function show_correct_answer() {
        clearInterval(game_interval);
        let full_card_elements = $("[id^=full_card_]");

        for (let i = 0; i < 4; ++i) {
            if (question == question_set[i]) {
                $(full_card_elements.get(i)).addClass("!border-green-800");
            } else {
                $(full_card_elements.get(i)).addClass("!border-red-800");
            }
        }

        setTimeout((_) => {
            let is_left = question_set.indexOf(question) % 2 === 0;
            reset_marsh(is_left);

            full_card_elements.removeClass("!border-green-800");
            full_card_elements.removeClass("!border-red-800");

            set_next_question_set();
            game_interval = setInterval(game_loop, 25);
        }, 1000);
    }

    function handle_game_over() {
        Swal.fire({
            title: "Game Over",
            html: `
            <div class="flex flex-col items-center">
            <div>
            <img src="/static/assets/crab_puddle.png">
            <div>
            <div class="mb-4">
                You answered ${num_correct} terms correctly.
            </div>
            <div class="mb-2">
                Keep reviewing the following terms:
            </div>
            <ul>
            ${wrong_questions.map(([k, v]) => `<li class="text-left"><a class="font-semibold">${k}</a>: ${v}</li>`).join("\n")}
            </ul>
            </div>`,
            confirmButtonText: "Play Again?",
        }).then((_) => {
            num_lives = max_lives;
            wrong_questions = [];
            set_next_question_set();
            game_interval = setInterval(game_loop, 25);
        });
    }

    $("[id^=full_card_]").on("click", function (_) {
        if (question == question_set[parseInt($(this).attr("id").slice(-1)) - 1]) {
            num_correct += 1;
            show_correct_answer();
        } 
    });

    set_next_question_set();
    let game_interval = setInterval(game_loop, 25);

    Swal.fire({
        title: "Ready to Play?",
        html: `<div class="flex flex-col items-center">
            <div class="my-4">
                Help the owls roast marshmallows by answering questions correctly!
            </div>
            </div>`,
        confirmButtonText: "Start Game",
    }).then(() => {});
});