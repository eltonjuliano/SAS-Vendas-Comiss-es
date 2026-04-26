import streamlit as st

@st.dialog("Confirm Dialog")
def confirm_dialog(os_id):
    st.write(f"Deseja excluir {os_id}?")
    if st.button("Sim"):
        st.write("Excluido!")
        st.query_params.clear()
        st.rerun()
    if st.button("Nao"):
        st.query_params.clear()
        st.rerun()

action = st.query_params.get("action")
os_id = st.query_params.get("os")

if action == "delete" and os_id:
    confirm_dialog(os_id)

st.write("Hello World")
st.markdown('<a href="/?action=delete&os=123" target="_self">🗑️ Excluir 123</a>', unsafe_allow_html=True)
