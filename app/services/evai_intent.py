def detect_intent(message):

    text = (
        message
        .lower()
        .strip()
    )


    intents = {

        "my_registrations": [
            "registered for",
            "my registrations",
            "my registered",
            "events i registered",
            "events i'm registered",
            "events i am registered",
            "which events did i register",
            "what did i register"
        ],

        "next_event": [
            "next event",
            "upcoming event",
            "next registered event",
            "what is my next"
        ],

        "event_location": [
            "where is my event",
            "where is the event",
            "event venue",
            "where will",
            "location of my event"
        ],

        "checkin": [
            "checked in",
            "check in",
            "did i attend",
            "did i go",
            "attendance"
        ],

        "certificates": [
            "my certificate",
            "my certificates",
            "certificate do i have",
            "certificates do i have"
        ],

        "my_reviews": [
            "my reviews",
            "reviews i gave",
            "what did i review",
            "events i reviewed",
            "which events have i reviewed"
        ],

        "campus_events": [
            "campus events",
            "events happening",
            "events happening on campus",
            "upcoming events",
            "what events are happening",
            "what events are there"
        ],

    }


    for intent, keywords in intents.items():

        for keyword in keywords:

            if keyword in text:
                return intent


    return "general"
