

/* =========================================================
   EvAi FLOATING ASSISTANT
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        const widget =
            document.getElementById(
                "evai-widget"
            );

        if (!widget) {
            return;
        }


        const floatButton =
            document.getElementById(
                "evai-float-button"
            );

        const chat =
            document.getElementById(
                "evai-chat"
            );

        const closeButton =
            document.getElementById(
                "evai-close"
            );

        const form =
            document.getElementById(
                "evai-chat-form"
            );

        const input =
            document.getElementById(
                "evai-input"
            );

        const messages =
            document.getElementById(
                "evai-messages"
            );

        const sendButton =
            document.getElementById(
                "evai-send"
            );


        function openChat() {

            chat.hidden = false;

            input.focus();

        }


        function closeChat() {

            chat.hidden = true;

        }


        function scrollMessages() {

            messages.scrollTop =
                messages.scrollHeight;

        }


        function addMessage(
            text,
            type
        ) {

            const wrapper =
                document.createElement(
                    "div"
                );

            wrapper.className =
                "evai-message " +
                (
                    type === "user"
                        ? "evai-message-user"
                        : "evai-message-ai"
                );


            const bubble =
                document.createElement(
                    "div"
                );

            bubble.className =
                "evai-message-bubble";

            bubble.textContent =
                text;


            wrapper.appendChild(
                bubble
            );

            messages.appendChild(
                wrapper
            );

            scrollMessages();

            return wrapper;

        }


        floatButton.addEventListener(
            "click",
            function () {

                if (chat.hidden) {
                    openChat();
                } else {
                    closeChat();
                }

            }
        );


        closeButton.addEventListener(
            "click",
            closeChat
        );


        document
            .querySelectorAll(
                "[data-evai-prompt]"
            )
            .forEach(
                function (button) {

                    button.addEventListener(
                        "click",
                        function () {

                            input.value =
                                button.dataset.evaiPrompt;

                            input.focus();

                        }
                    );

                }
            );


        form.addEventListener(
            "submit",
            async function (event) {

                event.preventDefault();


                const message =
                    input.value.trim();


                if (!message) {
                    return;
                }


                addMessage(
                    message,
                    "user"
                );


                input.value = "";

                input.disabled = true;
                sendButton.disabled = true;


                const typing =
                    addMessage(
                        "EvAi is thinking...",
                        "ai"
                    );

                typing.classList.add(
                    "evai-typing"
                );


                try {

                    const response =
                        await fetch(
                            "/ai/chat",
                            {
                                method: "POST",

                                headers: {
                                    "Content-Type":
                                        "application/json"
                                },

                                body:
                                    JSON.stringify({
                                        message:
                                            message
                                    })
                            }
                        );


                    const data =
                        await response.json();


                    typing.remove();


                    if (
                        !response.ok ||
                        !data.success
                    ) {

                        addMessage(
                            data.error ||
                            "EvAi could not process that request.",
                            "ai"
                        );

                        return;

                    }


                    addMessage(
                        data.answer,
                        "ai"
                    );


                } catch (error) {

                    typing.remove();

                    addMessage(
                        "I couldn't connect to EvAi right now. Please try again.",
                        "ai"
                    );

                    console.error(
                        "EvAi error:",
                        error
                    );

                } finally {

                    input.disabled = false;
                    sendButton.disabled = false;

                    input.focus();

                }

            }
        );

    }
);
