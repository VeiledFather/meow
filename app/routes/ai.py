from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import (
    login_required,
    current_user
)

from app.models import (
    Event,
    Review
)


ai_bp = Blueprint(
    "ai",
    __name__,
    url_prefix="/ai"
)


# =========================================================
# EvAi EVENT PLANNER
# =========================================================

@ai_bp.route(
    "/event-advisor",
    methods=["GET", "POST"]
)
@login_required
def event_advisor():

    if current_user.role != "organizer":

        return "Access denied", 403


    recommendation = None


    if request.method == "POST":

        event_type = request.form.get(
            "event_type",
            ""
        ).strip()

        event_title = request.form.get(
            "event_title",
            ""
        ).strip()

        expected_attendees = request.form.get(
            "expected_attendees",
            "0"
        ).strip()

        date = request.form.get(
            "date",
            ""
        ).strip()

        venue = request.form.get(
            "venue",
            ""
        ).strip()

        budget = request.form.get(
            "budget",
            ""
        ).strip()

        food_requirements = request.form.get(
            "food_requirements",
            ""
        ).strip()

        equipment_requirements = request.form.get(
            "equipment_requirements",
            ""
        ).strip()

        objectives = request.form.get(
            "objectives",
            ""
        ).strip()

        special_requirements = request.form.get(
            "special_requirements",
            ""
        ).strip()


        if not event_type or not expected_attendees or not date:

            flash(
                "Please provide the event type, date, and expected attendees.",
                "error"
            )

            return render_template(
                "organizer/ai_planner.html",
                recommendation=None
            )


        from app.services.evai import EVAI


        planner_prompt = f"""
You are EvAi Planner inside CampusHub.

Create a practical event plan for an organizer.

EVENT INFORMATION

Title:
{event_title or "Not specified"}

Event type:
{event_type}

Date:
{date}

Expected attendees:
{expected_attendees}

Venue:
{venue or "Not specified"}

Budget:
{budget or "Not specified"}

Food / catering requirements:
{food_requirements or "Not specified"}

Equipment requirements:
{equipment_requirements or "Not specified"}

Event objectives:
{objectives or "Not specified"}

Special requirements:
{special_requirements or "Not specified"}


Create useful recommendations for the organizer.

Consider:

1. Venue setup
2. Seating and attendee flow
3. Catering and approximate food planning
4. Equipment and technical requirements
5. Staffing and volunteer requirements
6. Suggested event schedule
7. Registration and check-in
8. Safety and contingency planning
9. Budget considerations
10. Practical organizer tips


Do not invent specific vendors, prices, regulations,
or campus facilities unless they were provided.

If information is missing, give a general recommendation
and clearly indicate that the organizer should confirm it.

Return ONLY valid JSON using exactly this structure:

{{
    "overview": "...",
    "venue": [
        "..."
    ],
    "catering": [
        "..."
    ],
    "equipment": [
        "..."
    ],
    "staffing": [
        "..."
    ],
    "schedule": [
        "..."
    ],
    "checkin": [
        "..."
    ],
    "safety": [
        "..."
    ],
    "budget": [
        "..."
    ],
    "tips": [
        "..."
    ]
}}
"""


        try:

            ai = EVAI()

            answer = ai.ask(
                message=planner_prompt,
                context=(
                    "The current user is an organizer "
                    "planning an event through CampusHub."
                )
            )


            import json


            cleaned = (
                answer
                .strip()
                .replace(
                    "```json",
                    ""
                )
                .replace(
                    "```",
                    ""
                )
                .strip()
            )


            recommendation = json.loads(
                cleaned
            )


            recommendation["event_title"] = (
                event_title
                or event_type
            )

            recommendation["event_type"] = (
                event_type
            )

            recommendation["date"] = (
                date
            )

            recommendation["expected_attendees"] = (
                expected_attendees
            )


        except Exception as exc:

            print(
                f"EvAi Planner error: {exc}"
            )

            flash(
                "EvAi could not generate the planner recommendations right now. Please try again.",
                "error"
            )


    return render_template(
        "organizer/ai_planner.html",
        recommendation=recommendation
    )


# =========================================================
# AI FEEDBACK ANALYSIS
# =========================================================

@ai_bp.route(
    "/feedback",
    methods=["GET", "POST"]
)
@login_required
def feedback_analysis():

    if current_user.role != "organizer":

        return "Access denied", 403


    from app.services.evai import EVAI


    events = (
        Event.query
        .filter_by(
            organizer_id=current_user.id
        )
        .order_by(
            Event.date.desc()
        )
        .all()
    )


    selected_event = None
    analysis = None


    if request.method == "POST":

        try:

            event_id = int(
                request.form.get(
                    "event_id",
                    0
                )
            )

        except (TypeError, ValueError):

            event_id = 0


        selected_event = (
            Event.query
            .filter_by(
                id=event_id,
                organizer_id=current_user.id
            )
            .first()
        )


        if not selected_event:

            flash(
                "Event not found.",
                "error"
            )

            return redirect(
                url_for(
                    "ai.feedback_analysis"
                )
            )


        reviews = (
            Review.query
            .filter_by(
                event_id=selected_event.id
            )
            .order_by(
                Review.created_at.asc()
            )
            .all()
        )


        # =================================================
        # BASIC STATISTICS
        # =================================================

        if not reviews:

            analysis = {

                "review_count": 0,

                "average_rating": 0,

                "positive": 0,

                "neutral": 0,

                "negative": 0,

                "themes": [],

                "recommendation": (
                    "There are no student reviews for "
                    "this event yet. Once attendees submit "
                    "feedback, EvAi will analyze their "
                    "ratings and comments."
                )

            }


        else:

            ratings = [
                review.rating
                for review in reviews
                if review.rating is not None
            ]


            total = len(
                reviews
            )


            average_rating = (
                sum(ratings) / len(ratings)
                if ratings
                else 0
            )


            positive_count = sum(
                1
                for review in reviews
                if review.rating >= 4
            )


            neutral_count = sum(
                1
                for review in reviews
                if review.rating == 3
            )


            negative_count = sum(
                1
                for review in reviews
                if review.rating <= 2
            )


            positive_percent = round(
                positive_count / total * 100
            )


            neutral_percent = round(
                neutral_count / total * 100
            )


            negative_percent = round(
                negative_count / total * 100
            )


            # =============================================
            # PREPARE REAL STUDENT FEEDBACK FOR EVAi
            # =============================================

            feedback_lines = []


            for number, review in enumerate(
                reviews,
                start=1
            ):

                comment = (
                    review.comment
                    or "No written comment."
                ).strip()


                feedback_lines.append(
                    f"Review {number}: "
                    f"Rating {review.rating}/5. "
                    f"Comment: {comment}"
                )


            feedback_text = "\n".join(
                feedback_lines
            )


            # =============================================
            # REAL EVAi ANALYSIS
            # =============================================

            ai = EVAI()


            analysis_prompt = f"""
Analyze the student feedback for this CampusHub event.

EVENT:
Title: {selected_event.title}
Type: {selected_event.event_type}
Date: {selected_event.date}
Venue: {selected_event.venue}

TOTAL REVIEWS:
{total}

AVERAGE RATING:
{round(average_rating, 1)}/5

RATING DISTRIBUTION:
Positive (4-5): {positive_percent}%
Neutral (3): {neutral_percent}%
Negative (1-2): {negative_percent}%

STUDENT REVIEWS:
{feedback_text}

Provide a concise but useful organizer analysis.

Identify:

1. The strongest aspects of the event.
2. What students liked most.
3. What went wrong or caused dissatisfaction.
4. The most important recurring themes.
5. Specific things the organizer should improve next time.
6. Things the organizer should keep doing.
7. A short overall recommendation.

Do not invent facts that are not present in the reviews.

Return ONLY valid JSON in this exact structure:

{{
    "strengths": [
        "..."
    ],
    "problems": [
        "..."
    ],
    "themes": [
        {{
            "name": "...",
            "mentions": 0
        }}
    ],
    "improvements": [
        "..."
    ],
    "keep_doing": [
        "..."
    ],
    "recommendation": "..."
}}
"""


            try:

                ai_answer = ai.ask(
                    message=analysis_prompt,
                    context=(
                        "You are analyzing real "
                        "CampusHub student reviews "
                        "for an organizer."
                    )
                )


                import json


                cleaned = (
                    ai_answer
                    .strip()
                    .replace(
                        "```json",
                        ""
                    )
                    .replace(
                        "```",
                        ""
                    )
                    .strip()
                )


                ai_analysis = json.loads(
                    cleaned
                )


            except Exception as exc:

                print(
                    f"EvAi feedback analysis error: {exc}"
                )


                ai_analysis = {

                    "strengths": [],

                    "problems": [],

                    "themes": [],

                    "improvements": [],

                    "keep_doing": [],

                    "recommendation": (
                        "EvAi could not complete the "
                        "detailed analysis right now. "
                        "The rating statistics above "
                        "are still available."
                    )

                }


            analysis = {

                "review_count":
                    total,

                "average_rating":
                    round(
                        average_rating,
                        1
                    ),

                "positive":
                    positive_percent,

                "neutral":
                    neutral_percent,

                "negative":
                    negative_percent,

                "themes":
                    ai_analysis.get(
                        "themes",
                        []
                    )[:5],

                "strengths":
                    ai_analysis.get(
                        "strengths",
                        []
                    ),

                "problems":
                    ai_analysis.get(
                        "problems",
                        []
                    ),

                "improvements":
                    ai_analysis.get(
                        "improvements",
                        []
                    ),

                "keep_doing":
                    ai_analysis.get(
                        "keep_doing",
                        []
                    ),

                "recommendation":
                    ai_analysis.get(
                        "recommendation",
                        "No recommendation generated."
                    )

            }


    return render_template(

        "organizer/feedback_analysis.html",

        events=events,

        selected_event=
            selected_event,

        analysis=
            analysis

    )


# =========================================================
# EVAi CHAT ASSISTANT
# =========================================================

@ai_bp.route(
    "/chat",
    methods=["POST"]
)
@login_required
def chat():

    from app.services.evai import EVAI
    from app.services.evai_context import get_user_context
    from app.services.evai_intent import detect_intent

    data = request.get_json(
        silent=True
    ) or {}

    message = (
        data.get("message", "")
        .strip()
    )

    if not message:

        return {
            "success": False,
            "error": "Please enter a message."
        }, 400


    role = current_user.role

    intent = detect_intent(
        message
    )

    context = get_user_context(
        current_user
    )

    context += (
        "\n\nDETECTED USER INTENT: "
        + intent
    )


    try:

        ai = EVAI()

        answer = ai.ask(
            message=message,
            context=context
        )

        return {
            "success": True,
            "answer": answer
        }


    except Exception as exc:

        print(
            f"EvAi error: {exc}"
        )

        return {
            "success": False,
            "error": (
                "EvAi is temporarily unavailable. "
                "Please try again."
            )
        }, 500

