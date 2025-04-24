import streamlit as st
from ui.states import AppState


def vendor_form() -> tuple[str, dict]:
    with st.form("vendor_cfg", clear_on_submit=False):
        vendor_name = st.text_input("Vendor name *", key="vendor_input")
        st.markdown("#### Optional filters")
        filters = {
            "product_category": st.text_input("Product / service"),
            "required_certs":  st.text_input("Certifications (comma-sep)"),
            "region":          st.text_input("Region"),
        }
        ok = st.form_submit_button("Run vendor research",
                                   type="primary",
                                   use_container_width=True)
    if ok and vendor_name:
        st.session_state.state = AppState.GENERATING_VENDOR
    return vendor_name, filters


def product_form() -> tuple[str, dict]:
    with st.form("product_cfg", clear_on_submit=False):
        category = st.text_input("Product / service category *",
                                 key="product_input")
        st.markdown("#### Optional filters")
        filters = {
            "required_certs": st.text_input("Certifications (comma-sep)"),
            "region":         st.text_input("Region"),
        }
        ok = st.form_submit_button("Run initial product analysis",
                                   type="primary",
                                   use_container_width=True)
    if ok and category:
        st.session_state.state = AppState.GENERATING_PRODUCT_INIT
    return category, filters 