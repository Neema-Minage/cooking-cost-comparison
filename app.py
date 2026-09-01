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

The interface is a thin layer: every number comes from engine.py, which is
unit-tested separately. Untested dish-appliance combinations are simply not
offered, so coverage gaps cannot be selected in the first place.
"""

import streamlit as st

from engine import MenuItem, Household, load_lookup, compare
from tariff import load_params


# ---------------------------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Household Cooking Cost Comparison — Kenya",
    page_icon="🍲",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# CUSTOM STYLING
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>

    /* Main page spacing */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* Main title */
    h1 {
        font-weight: 700;
        letter-spacing: -0.5px;
    }

    /* Section headings */
    h2, h3 {
        margin-top: 1.2rem;
    }

    /* Result cards */
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

    /* Big savings banner */
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

    /* Dish comparison cards */
    .dish-card {
        border: 1px solid rgba(128, 128, 128, 0.22);
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 8px;
        background: rgba(128, 128, 128, 0.025);
    }

    .dish-name {
        font-weight: 700;
        font-size: 1rem;
    }

    .dish-appliance {
        font-size: 0.84rem;
        opacity: 0.7;
        margin-top: 3px;
    }

    .dish-saving {
        font-weight: 700;
        font-size: 0.9rem;
        text-align: right;
    }

    /* Small explanatory text */
    .section-description {
        opacity: 0.68;
        font-size: 0.9rem;
        margin-top: -8px;
        margin-bottom: 15px;
    }

    /* Divider */
    .soft-divider {
        margin: 25px 0;
        border-top: 1px solid rgba(128, 128, 128, 0.18);
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        border-right: 1px solid rgba(128, 128, 128, 0.15);
    }

/* Cooking-choice grid */
.cooking-row {
    padding: 4px 0;
    margin-bottom: 2px;
}

/* Align labels and controls consistently */
div[data-testid="stHorizontalBlock"] {
    align-items: center;
}

/* Make selectboxes and number inputs visually consistent */
div[data-testid="stSelectbox"],
div[data-testid="stNumberInput"] {
    margin-bottom: 0;
}

/* Header styling */
.cooking-header {
    font-weight: 700;
    margin-bottom: 6px;
}


    </style>
    """
    ,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# DATA
# ---------------------------------------------------------------------------

DISHES = [
    "Beans",
    "Rice",
    "Spinach",
    "Chapati",
    "Chips",
]

DEFAULT_FREQ = {
    "Beans": 2,
    "Rice": 3,
    "Spinach": 4,
    "Chapati": 1,
    "Chips": 1,
}


@st.cache_data
def data():
    return load_lookup(), load_params()


lookup, params = data()


# ---------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------

def options_for(dish):
    """
    Return only appliances with tested and usable energy data.
    """
    return sorted(
        a
        for (d, a), rec in lookup.items()
        if d == dish and rec["energy_kwh"] is not None
    )


def money(value):
    """Format a value as Kenyan Shillings."""
    return f"KSh {value:,.0f}"


def signed_money(value):
    """Format a signed monetary difference."""
    if value < 0:
        return f"-KSh {abs(value):,.0f}"
    elif value > 0:
        return f"+KSh {value:,.0f}"
    return "KSh 0"


# ---------------------------------------------------------------------------
# HEADER
# ---------------------------------------------------------------------------

st.title("🍲 Household Cooking Cost Comparison")

st.caption(
    "Compare the monthly cost, energy use, cooking time and payback of "
    "different cooking appliances and fuels in Kenya."
)


# ---------------------------------------------------------------------------
# SIDEBAR — KEEPING YOUR ORIGINAL INPUT DESIGN
# ---------------------------------------------------------------------------

with st.sidebar:

    st.header("Your household")

    servings = st.slider(
        "Servings per meal",
        1,
        10,
        4,
    )

    baseline_kwh = st.number_input(
        "Current electricity use (kWh/month, excluding cooking)",
        min_value=0,
        max_value=500,
        value=45,
        help=(
            "From your KPLC bill or token purchases. Determines your tariff "
            "band — adding electric cooking can move you to a higher band, "
            "which this tool accounts for."
        ),
    )

    st.divider()

    st.caption(
        "Prices and tariffs are read from parameters.csv — edit that file "
        "to update them. Fuel prices vary by locality."
    )


# ---------------------------------------------------------------------------
# 1. COOKING CHOICES
# ---------------------------------------------------------------------------

st.subheader("1. What you cook, and on what")

st.markdown(
    """
    <div class="section-description">
    Choose how often you prepare each dish and compare your current appliance
    with the appliance you are considering.
    </div>
    """,
    unsafe_allow_html=True,
)

# Header row
header_dish, header_current, header_proposed = st.columns(
    [1.4, 2.0, 2.0],
    gap="medium",
)

with header_dish:
    st.markdown("**Dish / frequency**")

with header_current:
    st.markdown("**Current appliance**")

with header_proposed:
    st.markdown("**Considering instead**")


baseline_menu = []
proposed_menu = []


for dish in DISHES:

    opts = options_for(dish)

    # Safety check in case a dish has no tested appliance
    if not opts:
        st.warning(
            f"No tested appliance options are currently available for {dish}."
        )
        continue

    # ---------------------------------------------------------------
    # ONE CONSISTENT ROW
    # ---------------------------------------------------------------

    c0, c1, c2 = st.columns(
        [1.4, 2.0, 2.0],
        gap="medium",
    )

    # Dish + frequency
    with c0:
        freq = st.number_input(
            f"{dish} (times/week)",
            min_value=0.0,
            max_value=21.0,
            value=float(DEFAULT_FREQ[dish]),
            step=0.5,
            key=f"f_{dish}",
        )

    # Current appliance
    with c1:

        current_default = (
            opts.index("LPG stove")
            if "LPG stove" in opts
            else 0
        )

        cur = st.selectbox(
            f"Current {dish} appliance",
            opts,
            index=current_default,
            key=f"cur_{dish}",
        )

    # Proposed appliance
    with c2:

        prop_default = (
            "EPC"
            if "EPC" in opts
            else (
                "Induction cooker"
                if "Induction cooker" in opts
                else opts[0]
            )
        )

        prop = st.selectbox(
            f"Proposed {dish} appliance",
            opts,
            index=opts.index(prop_default),
            key=f"prop_{dish}",
        )

    # ---------------------------------------------------------------
    # BUILD MENUS
    # ---------------------------------------------------------------

    if freq > 0:

        baseline_menu.append(
            MenuItem(dish, cur, freq)
        )

        proposed_menu.append(
            MenuItem(dish, prop, freq)
        )

# ---------------------------------------------------------------------------
# 2. APPLIANCES TO BUY
# ---------------------------------------------------------------------------

st.subheader("2. Appliances you would need to buy")

proposed_apps = sorted(
    {m.appliance for m in proposed_menu}
)

current_apps = {
    m.appliance for m in baseline_menu
}

to_buy = st.multiselect(
    "Only appliances you don't already own count toward payback",
    proposed_apps,
    default=[
        a for a in proposed_apps
        if a not in current_apps
    ],
)


# ---------------------------------------------------------------------------
# CALCULATE RESULTS
# IMPORTANT: THIS MUST COME BEFORE THE RESULTS UI
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# RESULTS
# ---------------------------------------------------------------------------

st.divider()

st.subheader("3. Your cooking comparison")

st.markdown(
    """
    <div class="section-description">
    Here's what your current and proposed cooking choices mean for your household.
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# CALCULATED SUMMARY VALUES
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# MAIN RESULT
# ---------------------------------------------------------------------------

if monthly_savings > 0:

    st.markdown(
        f"""
        <div class="savings-banner">
            <div class="savings-title">
                💰 You could save {money(monthly_savings)} per month
            </div>
            <div class="savings-subtitle">
                That's approximately <strong>{money(annual_savings)}</strong>
                in savings over one year with the proposed cooking setup.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

elif monthly_savings < 0:

    st.warning(
        f"The proposed cooking setup costs "
        f"**{money(abs(monthly_savings))} more per month** "
        "than your current setup."
    )

else:

    st.info(
        "Your current and proposed cooking setups have approximately "
        "the same monthly cost."
    )


# ---------------------------------------------------------------------------
# CURRENT VS PROPOSED
# ---------------------------------------------------------------------------

st.markdown("### Monthly cooking cost")

cost_col1, arrow_col, cost_col2 = st.columns(
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


with arrow_col:

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


# ---------------------------------------------------------------------------
# VISUAL COST COMPARISON
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# KEY INDICATORS
# ---------------------------------------------------------------------------

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
        help=(
            "Monthly savings multiplied by 12 months."
        ),
    )


with k3:

    st.metric(
        "Cooking electricity",
        f"{p.cooking_kwh:.0f} kWh",
        delta=f"{energy_change:+.0f} kWh",
        help=(
            "Electricity used for cooking under "
            "the proposed setup."
        ),
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
            f"{out['payback_months']} months",
            help=(
                f"Upfront appliance cost: "
                f"{money(out['upfront_cost'])}"
            ),
        )


# ---------------------------------------------------------------------------
# ELECTRICITY IMPACT
# ---------------------------------------------------------------------------

if p.cooking_kwh:

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
                    {baseline_kwh:.0f} kWh
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
                    {total_electricity:.0f} kWh
                </div>
                <div class="card-small">
                    total household electricity per month
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.info(
        f"Electric cooking adds approximately "
        f"**{p.cooking_kwh:.0f} kWh/month**. "
        f"Your total electricity use would be about "
        f"**{total_electricity:.0f} kWh/month**, "
        f"placing you in the **{p.band}** tariff band. "
        "The tariff-band effect is already included "
        "in the proposed cost."
    )


# ---------------------------------------------------------------------------
# COOKING TIME
# ---------------------------------------------------------------------------

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


time_change = p.time_hours - b.time_hours

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




# ---------------------------------------------------------------------------
# 12-MONTH IMPACT
# ---------------------------------------------------------------------------

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




# ---------------------------------------------------------------------------
# DETAILED BREAKDOWN
# ---------------------------------------------------------------------------

with st.expander("🔍 View detailed cost breakdown"):

    detail_col1, detail_col2 = st.columns(2)

    with detail_col1:

        st.markdown("**Current cooking**")

        st.dataframe(
            [
                {
                    "Dish": e["dish"],
                    "Appliance": e["appliance"],
                    "KSh/month": e["monthly_cost"],
                }
                for e in b.items
            ],
            hide_index=True,
            width="stretch",
        )

        st.caption(
            f"Cooking time: "
            f"**{b.time_hours:.1f} hours/month**"
        )


    with detail_col2:

        st.markdown("**Proposed cooking**")

        st.dataframe(
            [
                {
                    "Dish": e["dish"],
                    "Appliance": e["appliance"],
                    "KSh/month": e["monthly_cost"],
                }
                for e in p.items
            ],
            hide_index=True,
            width="stretch",
        )

        st.caption(
            f"Cooking time: "
            f"**{p.time_hours:.1f} hours/month**"
        )


# ---------------------------------------------------------------------------
# DATA CAVEATS
# ---------------------------------------------------------------------------

warnings = (
    [
        f"{d} on {a}: {why}"
        for d, a, why
        in b.unavailable + p.unavailable
    ]
    +
    [
        (
            f"{e['dish']} on {e['appliance']}: "
            f"data flagged -- {e['flag'][:90]}"
        )
        for e in b.items + p.items
        if e["flag"]
    ]
)


if warnings:

    with st.expander(
        "⚠️ Things to know about this comparison"
    ):

        for warning in sorted(set(warnings)):

            st.warning(warning)



# ---------------------------------------------------------------------------
# FOOTER
# ---------------------------------------------------------------------------

st.divider()

st.caption(
    "Household Cooking Cost Comparison • Kenya • "
    "Costs shown in KSh per month"
)