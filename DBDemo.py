import streamlit as st
from supabase import create_client, Client

# Replace with your actual Supabase credentials
SUPABASE_URL = "https://bfuenejemwghgohoxdww.supabase.co"
SUPABASE_KEY = "sb_publishable_HoiAWdS_bE3E_WID4CKb1A_L_GNXO3A"

# Initialize Supabase client
@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

st.set_page_config(page_title="User Database", layout="centered")
st.title("📝 User Management App")

# Tabs for different sections
tab1, tab2 = st.tabs(["Add User", "View Users"])

# Tab 1: Add User
with tab1:
    st.subheader("Add a New User")
    
    with st.form("user_form"):
        name = st.text_input("Full Name", placeholder="John Doe")
        email = st.text_input("Email", placeholder="john@example.com")
        submit = st.form_submit_button("Add User")
        
        if submit:
            if name and email:
                try:
                    # Insert data into Supabase
                    response = supabase.table("users").insert({
                        "name": name,
                        "email": email
                    }).execute()
                    
                    st.success(f"✅ User '{name}' added successfully!")
                except Exception as e:
                    st.error(f"❌ Error adding user: {str(e)}")
            else:
                st.warning("Please fill in all fields")

# Tab 2: View Users
with tab2:
    st.subheader("All Users")
    
    try:
        # Fetch all users from Supabase
        response = supabase.table("users").select("*").execute()
        users = response.data
        
        if users:
            # Display as a table
            st.dataframe(users, use_container_width=True)
            
            # Delete user option
            st.subheader("Delete a User")
            user_ids = {user["name"]: user["id"] for user in users}
            selected_user = st.selectbox("Select user to delete", list(user_ids.keys()))
            
            if st.button("Delete User"):
                try:
                    supabase.table("users").delete().eq("id", user_ids[selected_user]).execute()
                    st.success(f"✅ User '{selected_user}' deleted successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error deleting user: {str(e)}")
        else:
            st.info("No users found. Add one in the 'Add User' tab!")
            
    except Exception as e:
        st.error(f"❌ Error fetching users: {str(e)}")
