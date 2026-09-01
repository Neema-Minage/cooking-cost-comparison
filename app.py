"""
app.py -- Streamlit interface for the Household Energy and Cost Comparison Tool.

Run locally:
    streamlit run app.py

Requires:
    streamlit
    engine.py
    tariff.py
    cct_lookup.csv
    parameters.csv
"""

import streamlit as st

from engine import MenuItem, Household, load_lookup, compare
from tariff import load_params


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Household Cooking Cost Comparison — Kenya",
    page_icon="🍲",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================================
# CUSTOM CSS
# ============================================================================

st.markdown(
    """
    <style>

    /* Page */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* Main headings */
    h1 {
        font-weight: 700;
        letter-spacing: -0.5px;
    }

    h2, h3 {
        margin-top: 1.2rem;
    }

    /* ---------------------------------------------------------
       THREE INPUT CARDS
       --------------------------------------------------------- */

    .choice-card {
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 14px;
        padding: 18px;
        background: rgba(128, 128, 128, 0.035);
        min-height: 105px;
        margin-bottom: 12px;
    }

    .choice-card-meals {
        border-top: 4px solid #d97706;
    }

    .choice-card-current {
        border-top: 4px solid #dc2626;
    }

    .choice-card-considering {
        border-top: 4px solid #2563eb;
    }

    .choice-card-title {
        font-size: 1.15rem;
        font-weight: 700;
        margin-bottom: 4px;
    }

    .choice-card-description {
        font-size: 0.85rem;
        color: #777;
        line-height: 1.35;
    }

    /* Make the columns equal height */
    div[data-testid="stHorizontalBlock"] {
        align-items: stretch;
    }

    /* ---------------------------------------------------------
       RESULT CARDS
       --------------------------------------------------------- */

    .result-card {
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 14px;
        padding: 20px;
        min-height: 125px;
        background: rgba(128, 128, 128, 0.04);
    }

    .result-card-primary {
        border: 2px solid #2e7d5b;
        border-radius: 14px;
        padding: 20px;
        min-height: 125px;
        background: rgba(46, 125, 91, 0.06);
    }

    .card-label {
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        opacity: 0.65;
        margin-bottom: 6px;
    }

    .card-value {
        font-size: 1.65rem;
        font-weight: 700;
        line-height: 1.2;
    }

    .card-small {
        font-size: 0.82rem;
        opacity: 0.65;
        margin-top: 5px;
    }

    /* ---------------------------------------------------------
       SAVINGS
       --------------------------------------------------------- */

    .savings-banner {
        border-radius: 14px;
        padding: 20px 24px;
        margin: 12px 0 20px 0;
        background: rgba(46, 125, 91, 0.08);
        border: 1px solid rgba(46, 125, 91, 0.25);
    }

    .savings-title {
        font-size: 1.25rem;
        font-weight: 700;
    }

    .savings-subtitle {
        font-size: 0.92rem;
        margin-top: 4px;
        opacity: 0.75;
    }

    /* ---------------------------------------------------------
       DESCRIPTION
       --------------------------------------------------------- */

    .section-description {
        opacity: 0.68;
        font-size: 0.9rem;
        margin-top: -8px;
        margin-bottom: 15px;
    }

    /* ---------------------------------------------------------
       DISH ROW
       --------------------------------------------------------- */

    .dish-row {
        border: 1px solid rgba(128, 128, 128, 0.18);
        border-radius: 10px;
        padding: 10px 12px;
        margin-bottom: 8px;
        background: rgba(128, 128, 128, 0.025);
    }

    /* ---------------------------------------------------------
       SIDEBAR
       --------------------------------------------------------- */

    section[data-testid="stSidebar"] {
        border-right: 1px solid rgba(128, 128, 128, 0.15);
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================================
# DATA
# ============================================================================

DISHES = [
    "Beans",
    "Beef stew",
    "Rice",
    "Ugali",
    "Spinach",
    "Chapati",
    "Chips",
]

DEFAULT_FREQ = {
    "Beans": 2,
    "Beef stew": 2,
    "Rice": 3,
    "Ugali": 3,
    "Spinach": 4,
    "Chapati": 1,
    "Chips": 1,
}


FREQUENCY_OPTIONS = [
    "Not cooked",
    "1 time/week",
    "2 times/week",
    "3 times/week",
    "4 times/week",
    "5 times/week",
    "6 times/week",
    "7 times/week",
    "10 times/week",
    "14 times/week",
    "21 times/week",
]


FREQUENCY_VALUES = {
    "Not cooked": 0,
    "1 time/week": 1,
    "2 times/week": 2,
    "3 times/week": 3,
    "4 times/week": 4,
    "5 times/week": 5,
    "6 times/week": 6,
    "7 times/week": 7,
    "10 times/week": 10,
    "14 times/week": 14,
    "21 times/week": 21,
}


# ============================================================================
# LOAD DATA
# ============================================================================

@st.cache_data
def load_data():
    lookup_data = load_lookup()
    params_data = load_params()
    return lookup_data, params_data


lookup, params = load_data()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def options_for(dish):
    """
    Return every appliance available for the selected dish.

    The appliance is included when the lookup contains usable energy data.
    """

    appliances = []

    for (d, appliance), record in lookup.items():

        if d != dish:
            continue

        energy = record.get("energy_kwh")

        if energy is None:
            continue

        appliances.append(appliance)

    return sorted(set(appliances))


def money(value):
    """Format Kenyan Shillings."""
    return f"KSh {value:,.0f}"


def frequency_to_number(label):
    """Convert frequency dropdown text into a numeric weekly frequency."""
    return FREQUENCY_VALUES.get(label, 0)


def default_frequency_label(dish):
    """Return the default frequency label for a dish."""

    value = DEFAULT_FREQ.get(dish, 1)

    if value == 1:
        return "1 time/week"

    return f"{value} times/week"


def default_current_appliance(options):
    """
    Prefer LPG stove when available.
    Otherwise use the first available appliance.
    """

    if "LPG stove" in options:
        return "LPG stove"

    return options[0] if options else None


def default_proposed_appliance(options):
    """
    Prefer EPC, then induction cooker, then another available appliance.
    """

    preferred = [
        "EPC",
        "Induction cooker",
        "Rice cooker",
        "Air fryer",
        "Infrared cooker",
        "Hot plate",
        "LPG stove",
        "Improved charcoal stove (ICS)",
        "Kerosene stove",
        "Ethanol stove",
    ]

    for appliance in preferred:

        if appliance in options:
            return appliance

    return options[0] if options else None


# ============================================================================
# HEADER
# ============================================================================

st.title("🍲 Household Cooking Cost Comparison")

st.caption(
    "Compare monthly cooking costs, energy use, cooking time and appliance "
    "payback for different cooking options in Kenya."
)


# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:

    st.header("Your household")

    servings = st.slider(
        "Servings per meal",
        min_value=1,
        max_value=10,
        value=4,
    )

    baseline_kwh = st.number_input(
        "Current electricity use (kWh/month, excluding cooking)",
        min_value=0,
        max_value=500,
        value=45,
        help=(
            "Enter your approximate household electricity use per month "
            "excluding cooking."
        ),
    )

    st.divider()

    st.caption(
        "Prices and tariffs are read from parameters.csv. "
        "Fuel prices can vary by location."
    )


# ============================================================================
# SECTION 1
# ============================================================================

st.subheader("1. Your cooking choices")

st.markdown(
    """
    <div class="section-description">
        Start by selecting the meals you cook. Then choose your current
        appliance and the appliance you are considering.
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================================
# THREE HORIZONTAL CARDS
# ============================================================================

card_meals, card_current, card_considering = st.columns(
    [1, 1, 1],
    gap="medium",
)


# ============================================================================
# CARD 1 — MEALS
# ============================================================================

with card_meals:

    st.markdown(
        """
        <div class="choice-card choice-card-meals">
            <div class="choice-card-title">
                🍽️ Meals
            </div>
            <div class="choice-card-description">
                Select the meals you cook and how often you cook them.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    selected_dishes = st.multiselect(
        "What do you cook?",
        options=DISHES,
        default=[],
        placeholder="Select one or more meals",
        key="meals_selection",
    )

    frequencies = {}

    if selected_dishes:

        st.markdown("**How often do you cook each meal?**")

        for dish in selected_dishes:

            default_label = default_frequency_label(dish)

            frequencies[dish] = st.selectbox(
                f"{dish} — frequency",
                options=FREQUENCY_OPTIONS,
                index=FREQUENCY_OPTIONS.index(default_label),
                key=f"frequency_{dish}",
            )

    else:

        st.info(
            "Select one or more meals to continue."
        )


# ============================================================================
# CARD 2 — CURRENT APPLIANCES
# ============================================================================

with card_current:

    st.markdown(
        """
        <div class="choice-card choice-card-current">
            <div class="choice-card-title">
                🔥 Current
            </div>
            <div class="choice-card-description">
                Select what you currently use for each meal.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    current_appliances = {}

    if not selected_dishes:

        st.info(
            "Your current appliances will appear here after you select meals."
        )

    else:

        for dish in selected_dishes:

            opts = options_for(dish)

            if not opts:

                st.warning(
                    f"No tested appliance data available for {dish}."
                )

                continue

            default_appliance = default_current_appliance(opts)

            default_index = (
                opts.index(default_appliance)
                if default_appliance in opts
                else 0
            )

            current_appliances[dish] = st.selectbox(
                f"{dish} — current appliance",
                options=opts,
                index=default_index,
                key=f"current_appliance_{dish}",
            )


# ============================================================================
# CARD 3 — CONSIDERING
# ============================================================================

with card_considering:

    st.markdown(
        """
        <div class="choice-card choice-card-considering">
            <div class="choice-card-title">
                ⚡ Considering
            </div>
            <div class="choice-card-description">
                Select the appliance you want to compare with your current one.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    proposed_appliances = {}

    if not selected_dishes:

        st.info(
            "Your proposed appliances will appear here after you select meals."
        )

    else:

        for dish in selected_dishes:

            opts = options_for(dish)

            if not opts:

                continue

            default_appliance = default_proposed_appliance(opts)

            default_index = (
                opts.index(default_appliance)
                if default_appliance in opts
                else 0
            )

            proposed_appliances[dish] = st.selectbox(
                f"{dish} — considering",
                options=opts,
                index=default_index,
                key=f"proposed_appliance_{dish}",
            )


# ============================================================================
# BUILD MENUS
# ============================================================================

baseline_menu = []
proposed_menu = []


for dish in selected_dishes:

    frequency_label = frequencies.get(
        dish,
        "Not cooked",
    )

    frequency = frequency_to_number(
        frequency_label
    )

    if frequency <= 0:
        continue

    current = current_appliances.get(dish)
    proposed = proposed_appliances.get(dish)

    if current is None or proposed is None:
        continue

    baseline_menu.append(
        MenuItem(
            dish,
            current,
            frequency,
        )
    )

    proposed_menu.append(
        MenuItem(
            dish,
            proposed,
            frequency,
        )
    )


# ============================================================================
# STOP HERE IF USER HAS NOT SELECTED A MEAL
# ============================================================================

if not selected_dishes:

    st.divider()

    st.info(
        "👆 Select at least one meal above to see the cooking comparison."
    )

    st.stop()


# ============================================================================
# IF MEALS WERE SELECTED BUT ALL ARE NOT COOKED
# ============================================================================

if not baseline_menu:

    st.divider()

    st.info(
        "Select a cooking frequency above to calculate your comparison."
    )

    st.stop()


# ============================================================================
# SECTION 2 — APPLIANCES TO BUY
# ============================================================================

st.subheader("2. Appliances you would need to buy")

proposed_apps = sorted(
    {
        item.appliance
        for item in proposed_menu
    }
)

current_apps = {
    item.appliance
    for item in baseline_menu
}

default_to_buy = [
    appliance
    for appliance in proposed_apps
    if appliance not in current_apps
]

to_buy = st.multiselect(
    "Select appliances you would need to purchase",
    options=proposed_apps,
    default=default_to_buy,
    key="appliances_to_buy",
)

st.caption(
    "Only appliances you do not already own count toward payback."
)


# ============================================================================
# CALCULATE
# ============================================================================

hh = Household(
    servings=servings,
    baseline_monthly_kwh=baseline_kwh,
)


out = compare(
    baseline_menu,
    proposed_menu,
    hh,
    lookup,
    params,
    new_appliances=tuple(to_buy),
)


b = out["baseline"]
p = out["proposed"]


# ============================================================================
# SECTION 3 — RESULTS
# ============================================================================

st.divider()

st.subheader("3. Your cooking comparison")

st.markdown(
    """
    <div class="section-description">
        Here's what your selected cooking choices mean for your household.
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================================
# CALCULATED VALUES
# ============================================================================

monthly_savings = out["monthly_savings"]

current_cost = b.total_cost
proposed_cost = p.total_cost

if current_cost > 0:

    savings_pct = (
        monthly_savings / current_cost
    ) * 100

else:

    savings_pct = 0


annual_savings = monthly_savings * 12
six_month_savings = monthly_savings * 6

energy_change = (
    p.cooking_kwh - b.cooking_kwh
)


# ============================================================================
# SAVINGS MESSAGE
# ============================================================================

if monthly_savings > 0:

    st.success(
        f"💰 You could save **{money(monthly_savings)} per month** "
        f"with the proposed cooking setup. "
        f"That's approximately **{money(annual_savings)} per year**."
    )

elif monthly_savings < 0:

    st.warning(
        f"The proposed cooking setup costs "
        f"**{money(abs(monthly_savings))} more per month** "
        f"than your current setup."
    )

else:

    st.info(
        "Your current and proposed cooking setups have approximately "
        "the same monthly cost."
    )


# ============================================================================
# MONTHLY COST
# ============================================================================

st.markdown("### Monthly cooking cost")

cost_col1, cost_arrow, cost_col2 = st.columns(
    [4, 1, 4]
)


with cost_col1:

    st.markdown(
        f"""
        <div class="result-card">
            <div class="card-label">Current cooking</div>
            <div class="card-value">{money(current_cost)}</div>
            <div class="card-small">per month</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with cost_arrow:

    st.markdown(
        """
        <div style="
            text-align:center;
            font-size:2rem;
            padding-top:32px;
            opacity:0.6;
        ">
            →
        </div>
        """,
        unsafe_allow_html=True,
    )


with cost_col2:

    st.markdown(
        f"""
        <div class="result-card-primary">
            <div class="card-label">Proposed cooking</div>
            <div class="card-value">{money(proposed_cost)}</div>
            <div class="card-small">per month</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================================
# COST PERCENTAGE
# ============================================================================

if monthly_savings > 0:

    st.markdown(
        f"""
        <div style="
            text-align:center;
            padding:12px;
            margin:10px 0 20px 0;
            border-radius:10px;
            background:rgba(46,125,91,0.07);
            font-size:1rem;
        ">
            <strong>{money(monthly_savings)} saved every month</strong>
            &nbsp; • &nbsp;
            {savings_pct:.0f}% lower cooking cost
        </div>
        """,
        unsafe_allow_html=True,
    )

elif monthly_savings < 0:

    st.markdown(
        f"""
        <div style="
            text-align:center;
            padding:12px;
            margin:10px 0 20px 0;
            border-radius:10px;
            background:rgba(200,60,60,0.07);
            font-size:1rem;
        ">
            <strong>{money(abs(monthly_savings))} more per month</strong>
            &nbsp; • &nbsp;
            {abs(savings_pct):.0f}% higher cooking cost
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================================
# AT A GLANCE
# ============================================================================

st.markdown("### At a glance")

k1, k2, k3, k4 = st.columns(4)


with k1:

    st.metric(
        "Monthly savings",
        money(monthly_savings),
        delta=(
            f"{savings_pct:.0f}%"
            if current_cost > 0
            else None
        ),
    )


with k2:

    st.metric(
        "Annual impact",
        money(annual_savings),
    )


with k3:

    st.metric(
        "Cooking electricity",
        f"{p.cooking_kwh:.1f} kWh",
        delta=f"{energy_change:+.1f} kWh",
    )


with k4:

    if out["payback_months"] is None:

        st.metric(
            "Payback",
            "Never",
        )

    elif out["payback_months"] == 0:

        st.metric(
            "Payback",
            "No purchase",
        )

    else:

        st.metric(
            "Payback",
            f"{out['payback_months']:.1f} months",
        )


# ============================================================================
# ELECTRICITY IMPACT
# ============================================================================

if p.cooking_kwh > 0:

    st.markdown("### ⚡ Electricity impact")

    tariff_col1, tariff_col2 = st.columns(2)

    total_electricity = (
        baseline_kwh + p.cooking_kwh
    )

    with tariff_col1:

        st.markdown(
            f"""
            <div class="result-card">
                <div class="card-label">
                    Current electricity use
                </div>
                <div class="card-value">
                    {baseline_kwh:.1f} kWh
                </div>
                <div class="card-small">
                    per month, excluding cooking
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


    with tariff_col2:

        st.markdown(
            f"""
            <div class="result-card-primary">
                <div class="card-label">
                    With proposed electric cooking
                </div>
                <div class="card-value">
                    {total_electricity:.1f} kWh
                </div>
                <div class="card-small">
                    total household electricity per month
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


    # Do not assume every result object has a tariff band.
    band = getattr(
        p,
        "band",
        None,
    )

    if band:

        st.info(
            f"Electric cooking adds approximately "
            f"**{p.cooking_kwh:.1f} kWh/month**. "
            f"Your total electricity use would be about "
            f"**{total_electricity:.1f} kWh/month**, "
            f"placing you in the **{band}** tariff band."
        )

    else:

        st.info(
            f"Electric cooking adds approximately "
            f"**{p.cooking_kwh:.1f} kWh/month**. "
            f"Your total electricity use would be about "
            f"**{total_electricity:.1f} kWh/month**."
        )


# ============================================================================
# COOKING TIME
# ============================================================================

st.markdown("### ⏱ Cooking time")

time_col1, time_arrow, time_col2 = st.columns(
    [4, 1, 4]
)


with time_col1:

    st.markdown(
        f"""
        <div class="result-card">
            <div class="card-label">Current</div>
            <div class="card-value">
                {b.time_hours:.1f} h
            </div>
            <div class="card-small">
                cooking time per month
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with time_arrow:

    st.markdown(
        """
        <div style="
            text-align:center;
            font-size:2rem;
            padding-top:32px;
            opacity:0.6;
        ">
            →
        </div>
        """,
        unsafe_allow_html=True,
    )


with time_col2:

    st.markdown(
        f"""
        <div class="result-card-primary">
            <div class="card-label">Proposed</div>
            <div class="card-value">
                {p.time_hours:.1f} h
            </div>
            <div class="card-small">
                cooking time per month
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


time_change = (
    p.time_hours - b.time_hours
)


if time_change < 0:

    st.success(
        f"The proposed setup could reduce cooking time by "
        f"**{abs(time_change):.1f} hours per month**."
    )

elif time_change > 0:

    st.info(
        f"The proposed setup increases cooking time by "
        f"**{time_change:.1f} hours per month**."
    )

else:

    st.info(
        "Cooking time is approximately the same."
    )


# ============================================================================
# LONG-TERM IMPACT
# ============================================================================

st.markdown("### 💰 What this means over time")

impact1, impact2, impact3 = st.columns(3)


with impact1:

    st.markdown(
        f"""
        <div class="result-card">
            <div class="card-label">After 1 month</div>
            <div class="card-value">
                {money(monthly_savings)}
            </div>
            <div class="card-small">
                cumulative difference
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with impact2:

    st.markdown(
        f"""
        <div class="result-card">
            <div class="card-label">After 6 months</div>
            <div class="card-value">
                {money(six_month_savings)}
            </div>
            <div class="card-small">
                cumulative difference
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with impact3:

    st.markdown(
        f"""
        <div class="result-card-primary">
            <div class="card-label">After 12 months</div>
            <div class="card-value">
                {money(annual_savings)}
            </div>
            <div class="card-small">
                cumulative difference
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================================
# DETAILED BREAKDOWN
# ============================================================================

with st.expander("🔍 View detailed cost breakdown"):

    detail_col1, detail_col2 = st.columns(2)


    with detail_col1:

        st.markdown("**Current cooking**")

        current_rows = [
            {
                "Dish": item["dish"],
                "Appliance": item["appliance"],
                "KSh/month": item["monthly_cost"],
            }
            for item in b.items
        ]

        if current_rows:

            st.dataframe(
                current_rows,
                hide_index=True,
                width="stretch",
            )

        else:

            st.info("No current cooking data.")


        st.caption(
            f"Cooking time: **{b.time_hours:.1f} hours/month**"
        )


    with detail_col2:

        st.markdown("**Proposed cooking**")

        proposed_rows = [
            {
                "Dish": item["dish"],
                "Appliance": item["appliance"],
                "KSh/month": item["monthly_cost"],
            }
            for item in p.items
        ]

        if proposed_rows:

            st.dataframe(
                proposed_rows,
                hide_index=True,
                width="stretch",
            )

        else:

            st.info("No proposed cooking data.")


        st.caption(
            f"Cooking time: **{p.time_hours:.1f} hours/month**"
        )


# ============================================================================
# DATA WARNINGS
# ============================================================================

warnings = []


for dish, appliance, why in b.unavailable + p.unavailable:

    warnings.append(
        f"{dish} on {appliance}: {why}"
    )


for item in b.items + p.items:

    flag = item.get("flag")

    if flag:

        warnings.append(
            f"{item['dish']} on {item['appliance']}: "
            f"data flagged — {flag[:120]}"
        )


if warnings:

    with st.expander(
        "⚠️ Things to know about this comparison"
    ):

        for warning in sorted(set(warnings)):

            st.warning(warning)


# ============================================================================
# FOOTER
# ============================================================================

st.divider()

st.caption(
    "Household Cooking Cost Comparison • Kenya • "
    "Costs shown in KSh per month"
)