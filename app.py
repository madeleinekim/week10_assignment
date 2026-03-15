import json
import os
import time
import uuid

import requests
import streamlit as st

st.set_page_config(page_title="My AI Chat", layout="wide")

HF_API_URL = "https://router.huggingface.co/v1/chat/completions"
HF_MODEL = "meta-llama/Llama-3.2-1B-Instruct"
CHATS_DIR = "chats"
MEMORY_FILE = "memory.json"
MEMORY_SYSTEM_PROMPT = (
    "You are a memory extractor. Given the following conversation, extract key user "
    "preferences, traits, or facts (e.g., name, interests, style) and return them ONLY "
    "as a valid JSON object. If nothing new is found, return {}."
)


def ensure_chats_dir() -> None:
    if os.path.isfile(CHATS_DIR):
        st.error("A file named 'chats' exists. Please rename or delete it, then reload the app.")
        st.stop()
    if not os.path.isdir(CHATS_DIR):
        os.makedirs(CHATS_DIR, exist_ok=True)


def chat_file_path(chat_id: str) -> str:
    return os.path.join(CHATS_DIR, f"{chat_id}.json")


def save_chat(chat_id: str) -> None:
    chat = st.session_state.chats.get(chat_id)
    if not chat:
        return
    payload = {
        "id": chat_id,
        "title": chat.get("title", "New Chat"),
        "messages": chat.get("messages", []),
    }
    with open(chat_file_path(chat_id), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def load_chats() -> None:
    ensure_chats_dir()
    for filename in os.listdir(CHATS_DIR):
        if not filename.endswith(".json"):
            continue
        path = os.path.join(CHATS_DIR, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue

        chat_id = data.get("id") or os.path.splitext(filename)[0]
        title = data.get("title", "New Chat")
        messages = data.get("messages", [])
        st.session_state.chats[chat_id] = {
            "title": title,
            "messages": messages,
        }


def load_memory() -> dict:
    if not os.path.exists(MEMORY_FILE):
        return {}
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except (OSError, json.JSONDecodeError):
        return {}
    return {}


def save_memory(memory: dict) -> None:
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)


def merge_memory(existing: dict, new_data: dict) -> dict:
    merged = dict(existing)
    for key, value in new_data.items():
        merged[key] = value
    return merged


def build_messages_with_memory(messages: list[dict], memory: dict) -> list[dict]:
    if not memory:
        return messages
    system_content = (
        "You are a helpful assistant. Here is what you know about the user: "
        f"{json.dumps(memory, ensure_ascii=False)}"
    )
    return [{"role": "system", "content": system_content}] + messages


def stream_hf_router(messages: list[dict], token: str, placeholder: st.delta_generator.DeltaGenerator) -> str:
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": HF_MODEL,
        "messages": messages,
        "stream": True,
    }

    try:
        response = requests.post(
            HF_API_URL,
            headers=headers,
            json=payload,
            stream=True,
            timeout=(10, 60),
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        return f"Request failed: {exc}"

    full_text = ""
    try:
        for raw_line in response.iter_lines(decode_unicode=True):
            if not raw_line:
                continue

            line = raw_line.strip()
            if not line.startswith("data:"):
                continue

            data_str = line[5:].strip()
            if data_str == "[DONE]":
                break

            try:
                data = json.loads(data_str)
            except json.JSONDecodeError:
                continue

            try:
                delta = data["choices"][0]["delta"]
                chunk = delta.get("content", "")
            except (KeyError, IndexError, TypeError):
                chunk = ""

            if chunk:
                full_text += chunk
                placeholder.write(full_text)
                time.sleep(0.01)
    except requests.RequestException as exc:
        return f"Stream interrupted: {exc}"

    if not full_text:
        return "No response text received."

    return full_text


def extract_memory(messages: list[dict], token: str) -> dict:
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": HF_MODEL,
        "messages": [
            {"role": "system", "content": MEMORY_SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(messages, ensure_ascii=False)},
        ],
    }

    try:
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
    except requests.RequestException:
        return {}

    try:
        data = response.json()
        content = data["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError):
        return {}

    try:
        extracted = json.loads(content)
    except json.JSONDecodeError:
        return {}

    return extracted if isinstance(extracted, dict) else {}


def create_new_chat() -> None:
    chat_id = str(uuid.uuid4())
    st.session_state.chats[chat_id] = {"title": "New Chat", "messages": []}
    st.session_state.current_chat_id = chat_id
    save_chat(chat_id)


def ensure_initialized() -> None:
    if "chats" not in st.session_state:
        st.session_state.chats = {}

    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = None

    if "loaded_chats" not in st.session_state:
        st.session_state.loaded_chats = True
        load_chats()

    if "memory" not in st.session_state:
        st.session_state.memory = load_memory()

    if not st.session_state.chats:
        create_new_chat()


def set_chat_title_from_first_message(chat_id: str, message: str) -> None:
    chat = st.session_state.chats.get(chat_id)
    if not chat:
        return
    if chat.get("title") != "New Chat":
        return
    snippet = message.strip().replace("\n", " ")
    if len(snippet) > 30:
        snippet = snippet[:30].rstrip() + "..."
    if snippet:
        chat["title"] = snippet
        save_chat(chat_id)


hf_token = st.secrets.get("HF_TOKEN", "")
if not hf_token:
    st.error("Missing HF_TOKEN. Please check your Streamlit secrets file.")
    st.stop()

ensure_initialized()

with st.sidebar:
    st.button("New Chat", on_click=create_new_chat)
    st.write("Chats")

    for chat_id, chat in list(st.session_state.chats.items()):
        cols = st.columns([0.85, 0.15])
        title = chat["title"]
        label = f"{title} [Active]" if chat_id == st.session_state.current_chat_id else title

        if cols[0].button(label, key=f"select_{chat_id}"):
            st.session_state.current_chat_id = chat_id

        if cols[1].button("✕", key=f"delete_{chat_id}"):
            del st.session_state.chats[chat_id]
            try:
                os.remove(chat_file_path(chat_id))
            except OSError:
                pass
            if st.session_state.current_chat_id == chat_id:
                remaining_ids = list(st.session_state.chats.keys())
                if remaining_ids:
                    st.session_state.current_chat_id = remaining_ids[0]
                else:
                    create_new_chat()
            st.rerun()

    with st.expander("User Memory", expanded=False):
        if st.session_state.memory:
            st.json(st.session_state.memory)
        else:
            st.write("No memory stored yet.")

    if st.button("Clear Memory"):
        st.session_state.memory = {}
        save_memory(st.session_state.memory)
        st.rerun()

current_chat = st.session_state.chats.get(st.session_state.current_chat_id)
if not current_chat:
    create_new_chat()
    current_chat = st.session_state.chats[st.session_state.current_chat_id]

for message in current_chat["messages"]:
    with st.chat_message(message["role"]):
        st.write(message["content"])

user_message = st.chat_input("Type your message")
if user_message:
    current_chat["messages"].append({"role": "user", "content": user_message})
    set_chat_title_from_first_message(st.session_state.current_chat_id, user_message)
    save_chat(st.session_state.current_chat_id)
    with st.chat_message("user"):
        st.write(user_message)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        contextual_messages = build_messages_with_memory(
            current_chat["messages"], st.session_state.memory
        )
        assistant_reply = stream_hf_router(contextual_messages, hf_token, placeholder)

    current_chat["messages"].append({"role": "assistant", "content": assistant_reply})
    save_chat(st.session_state.current_chat_id)

    new_memory = extract_memory(current_chat["messages"], hf_token)
    if new_memory:
        st.session_state.memory = merge_memory(st.session_state.memory, new_memory)
        save_memory(st.session_state.memory)
