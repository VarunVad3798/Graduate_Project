import streamlit as st
import requests
import subprocess
import os
import re
from datetime import datetime

# --- Functions ---
def extract_plantuml_block(text):
    matches = re.findall(r'@startuml.*?@enduml', text, re.DOTALL)
    if matches:
        # Pick first @startuml block
        return matches[0]
    raise ValueError("⚠️ No @startuml block detected in API response.")

def fix_script(script):
    script = script.replace('->>', '->')
    script = script.replace('..>', '-->')
    script = script.replace('..>o--', '-->')
    script = script.replace('o--', '--')
    script = re.sub(r'(@startuml\s*)+', '@startuml\n', script)  # clean duplicate @startuml
    return script

def get_plantuml_script(prompt):
    url = "http://csai01:8000/generate/"
    payload = {
        "prompt": f"Return only the PlantUML code for this user requirement without explanation:\n{prompt}",
        "max_tokens": 1024
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        data = response.json()
        return data.get("response", {}).get("content", "")
    raise ConnectionError(f"Request failed: {response.status_code}")

def generate_diagram(script, output_dir="diagrams"):
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    puml_path = os.path.join(output_dir, f"uml_output_{timestamp}.puml")
    png_path = puml_path.replace(".puml", ".png")

    with open(puml_path, 'w', encoding='utf-8') as f:
        f.write(script)

    subprocess.run(["java", "-jar", "plantuml.jar", puml_path], check=True)
    return png_path, puml_path

# --- Streamlit App ---
st.set_page_config(page_title="PlantUML Auto Generator", page_icon="🌟")

st.title("🌟 Auto Diagram Generator")
st.caption("Enter a simple description like: 'Draw a class diagram for a banking app.' No need to mention PlantUML!")

user_prompt = st.text_area("✍️ Your Prompt:", height=200)

if st.button("🚀 Generate Diagram"):
    if user_prompt.strip() == "":
        st.warning("⚠️ Please enter a prompt first.")
    else:
        try:
            raw = get_plantuml_script(user_prompt)

            puml_script = extract_plantuml_block(raw)
            final_script = fix_script(puml_script)

            output_image, puml_file = generate_diagram(final_script)

            st.success("✅ Diagram generated successfully!")
            st.image(output_image)

            # Download buttons
            with open(output_image, "rb") as img_file:
                st.download_button("📥 Download Diagram (PNG)", img_file, file_name="diagram.png", mime="image/png")
            with open(puml_file, "rb") as puml_file_open:
                st.download_button("📥 Download Script (.puml)", puml_file_open, file_name="diagram.puml", mime="text/plain")

        except Exception as e:
            st.error(f"⚠️ Error: {str(e)}")


