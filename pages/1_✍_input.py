import streamlit as st

# used for types
from typing import List, Optional, Set, Dict
from enum import Enum

#  from dataclasses import dataclass
from pydantic import Field, ValidationError, validator
from pydantic.dataclasses import dataclass
#  from pydantic.json import pydantic_encoder
#  import json
import streamlit_pydantic as sp

# used for multiselections
Stop_Categories = {
    "Category1" : ["Reason11", "Reason12"],
    "Category2" : ["Reason21", "Reason22"],
    "Category3" : ["Reason31", "Reason32"],
    "Category4" : ["Reason41", "Reason42"],
}

# let's use pydantic to make forms
# defining input form class
@dataclass
class e_class:
    E1: int = Field(..., description="Tag E1")
    E2: int = Field(..., description="Tag E2")
    # best to use the slider syntax to enforce int type and limits!
    E3: int = Field(
        0,
        ge=0,
        lt=30,
        multiple_of=2,
        description="Tag E3",
    )
    E4: int = Field(
        0,
        ge=0,
        lt=30,
        multiple_of=2,
        description="Tag E4",
    )
    E4_state: bool = False,
    E_comment: str = "no comment"

# adding a seession state dictionary to keep track of calculated values
if 'calculated' not in st.session_state:
    st.session_state['calculated'] = {}
scalc = st.session_state["calculated"]

with st.expander("E form data"):
    e_data = sp.pydantic_form(key="e", model=e_class)

    if e_data:
        st.success("Data saved!")
        # calculations can be performed here too:
        scalc['E_sum'] = e_data.E1 + e_data.E2 + e_data.E3 + e_data.E4

with st.expander("P form data"):
    # NOTE: selectbox based on selectbox should not be placed in st.form
    #       because submit has to be pressed to update the 2nd box
    FIQ = st.slider("Steam temperature", 100, 300, 100, 10)
    FIQ_running_hours = st.slider("Running hours for Steam Pump", 0,200,0)
    P_comment = st.text_area(value="no comment", label="Please insert a comment")
    P_stop_category = st.selectbox(
            "Stop category", options=list(Stop_Categories), index=None,
    )
    if P_stop_category:
        P_stop_reason = st.multiselect( "Stop reason", options=Stop_Categories[P_stop_category])
    else:
        P_stop_reason = []
        # st.warning("Please select category")
        # st.warning("Please select reason as well; then click submit")

    submit_button = st.button(label="Submit")
    if submit_button:
        st.success("Data saved!")
        st.session_state['p-data'] = {
            "FIQ" : FIQ,
            "FIQ_running_hours" : FIQ_running_hours,
            "P_comment" : P_comment,
            "P_stop_category" : P_stop_category,
            "P_stop_reason" : P_stop_reason
        }

with st.expander("Check session state"):
    st.write(st.session_state)

