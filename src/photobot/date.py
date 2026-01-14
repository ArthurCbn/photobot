from photobot.parameters import DATE_GROUP_DATA_PATH
import pandas as pd
import streamlit as st

# region HANDLE CSV

existing_groups = pd.DataFrame(columns=["nom", "date_debut", "date_fin", "full_day"])
if DATE_GROUP_DATA_PATH.exists() :
    existing_groups = pd.read_csv(DATE_GROUP_DATA_PATH)

existing_groups["nom"] = existing_groups["nom"].astype("string")
existing_groups["date_debut"] = pd.to_datetime(existing_groups["date_debut"])
existing_groups["date_fin"] = pd.to_datetime(existing_groups["date_fin"])
existing_groups["full_day"] = existing_groups["full_day"].astype("bool")

existing_groups = existing_groups.sort_values("date_debut").reset_index(drop=True)

# endregion

# region UI

st.title("Photobot")
st.subheader("Groupes par dates")

# region |---| Tweaks

st.set_page_config(layout="wide")

st.markdown("""
        <style>
            [data-testid="stToolbar"] {
                display: none;
            }
        </style>
    """, unsafe_allow_html=True)

st.markdown("""
    <style>
        [data-testid="stMainBlockContainer"] {
            padding-top: 2rem;
        }
    </style>
""", unsafe_allow_html=True)

# endregion

edited_df = st.data_editor(
    existing_groups,
    hide_index=True,
    num_rows="dynamic",
    column_config={
        "nom": st.column_config.TextColumn(
            "Nom",
            required=True
        ),
        "date_debut": st.column_config.DatetimeColumn(
            "Date de début",
            format="DD/MM/YYYY HH:mm:ss",
            required=True
        ),
        "date_fin": st.column_config.DatetimeColumn(
            "Date de fin",
            format="DD/MM/YYYY HH:mm:ss",
            required=True
        ),
        "full_day": st.column_config.CheckboxColumn(
            "Journée entière"
        )
    },
    width="stretch",
    height=500
)

if st.button("Sauvegarder") :
    edited_df.to_csv(DATE_GROUP_DATA_PATH)

# endregion