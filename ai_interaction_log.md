Task 1 Part A: [Page Setup & API Connection]
**Prompt:** I am working on a Streamlit app that connects to the Hugging Face Inference Router API. Please help me write the code for app.py based on these requirements:
Page Configuration: Use st.set_page_config with the title 'My AI Chat' and a 'wide' layout.
Secrets Management: Load my Hugging Face token from st.secrets["HF_TOKEN"].
Error Handling: If the token is missing or empty, use st.error to tell the user to check their secrets file. The app should not crash.
API Connection: Create a function that sends a POST request to https://router.huggingface.co/v1/chat/completions. Use the model meta-llama/Llama-3.2-1B-Instruct.
Initial Test: When the app runs, send a hardcoded test message "Hello!" to the API and use st.write to display the response in the main area.
Graceful Failure: Wrap the API request in a try-except block to handle potential network or rate-limit errors gracefully.
Please use the requests library for the API call as specified in my assignment.
**AI Suggestion:** The AI provided a Python script using streamlit and requests. it defined a function get_hf_response(messages) that sets up the proper headers (Authorization with Bearer token) and payload. It also included logic to check if "HF_TOKEN" not in st.secrets at the start of the app to prevent crashes.
**My Modifications & Reflections:** ode worked as provided.

Task 1 Part B: [Multi-Turn Conversation UI]
**Prompt:** I have the basic API connection working in my Streamlit app. Now, please help me update app.py for Task 1 Part B with these requirements:
Session State: Initialize st.session_state.messages as an empty list if it doesn't exist yet.
Display History: Use a for loop and st.chat_message to render every message currently stored in st.session_state.messages.
Chat Input: Use st.chat_input to collect a new message from the user.
Update History: When the user sends a message:
Append the user's message to st.session_state.messages.
Immediately display that message using st.chat_message.
API Call with Context: Send the entire list of st.session_state.messages to the Hugging Face API (https://router.huggingface.co/v1/chat/completions) so the model has the full conversation context.
Handle Response: Append the assistant's response to st.session_state.messages and display it in the chat UI.
Constraints: Use the requests library. Ensure the input bar stays fixed at the bottom while the chat history is scrollable.
**AI Suggestion:** The AI suggested using st.session_state to store a list of dictionaries with role and content keys. It provided a loop to render existing messages using st.chat_message before the st.chat_input logic. It also updated the API payload to use the entire list from st.session_state.messages instead of a single hardcoded string.
**My Modifications & Reflections:** Code worked as provided.

Task 1 Part C: [Chat Management]
**Prompt:** I have a working multi-turn chat app in Streamlit. Now, please help me update app.py for Task 1 Part C with these requirements:
Sidebar Structure: Use st.sidebar to create a 'New Chat' button at the top.
Multiple Chat Storage: Instead of one messages list, update st.session_state to store a dictionary of chats (e.g., st.session_state.chats = {}). Each chat should have a unique ID, a title, and its own messages list.
Active Chat Tracking: Create a variable st.session_state.current_chat_id to track which chat is currently being viewed.
Chat Navigation: In the sidebar, display a list of all existing chats. Use st.button or st.selectbox for the user to select a chat. The active chat should be visually distinct or highlighted.
New Chat Logic: When the 'New Chat' button is clicked:
Generate a new unique ID (using uuid or a timestamp).
Initialize a new empty message list for that ID.
Set this new ID as the current_chat_id.
Delete Functionality: Add a '✕' button next to each chat name in the sidebar. Clicking it should remove that chat from st.session_state.chats.
Dynamic Rendering: Ensure the main chat window always displays the messages associated with the current_chat_id.
Constraints: Use only native Streamlit components (no custom CSS). Use the requests library for the API calls
**AI Suggestion:** The AI recommended restructuring st.session_state to hold a dictionary called chats. It suggested using uuid or time.time() for unique keys. It provided a sidebar loop to generate navigation buttons and a logic block to switch the current_chat_id when a button is pressed. It also included a del st.session_state.chats[chat_id] snippet for the deletion feature.
**My Modifications & Reflections:** Code worked as provided.

Task 1 Part D: [Chat Persistence]
**Prompt:** I have a Streamlit app that manages multiple chats in st.session_state. Now, please help me implement Task 1 Part D: Chat Persistence with these requirements:
File Structure: Ensure there is logic to check for a directory named chats/ in the project folder and create it if it doesn't exist.
Saving Chats: Create a function save_chat(chat_id) that takes the chat data (ID, title, and message history) from st.session_state and saves it as a JSON file inside the chats/ folder (e.g., chats/{chat_id}.json).
Loading on Startup: When the app first runs, use the os library to list all files in the chats/ folder. Load each JSON file back into st.session_state.chats so they appear in the sidebar automatically.
Auto-Save: Update the chat logic so that every time the user sends a message or the assistant responds, the save_chat function is called to keep the file up to date.
Title Generation: When a new chat is created, use the first 20-30 characters of the first user message as a temporary title, or ask the AI to summarize it into a short title.
Persistent Deletion: Update the delete button logic so that clicking it also deletes the corresponding .json file from the chats/ folder using os.remove().
Refinement: Ensure that switching between loaded chats correctly populates the main chat window with that specific file's message history.
**AI Suggestion:** The AI provided functions using the json library to dump and load dictionaries. it used os.makedirs to ensure the chats/ folder exists and os.listdir to populate the sidebar on startup.
**My Modifications & Reflections:** Code worked as provided.


Task 2: [Response Streaming]
**Prompt:** I have a working multi-turn chat app with persistence. Now, please help me implement Task 2: Response Streaming with these requirements:
API Update: Update the requests.post call to the Hugging Face Inference Router by adding stream=True to the payload and the function call itself.
Streaming Logic: Instead of using response.json(), use response.iter_lines() to process the Server-Sent Events (SSE) stream.
UI Rendering: Use a Streamlit placeholder (st.empty()) or st.write_stream() to display the text incrementally as chunks arrive.
Handling SSE Format: Parse each line that starts with data:. Handle the [DONE] signal gracefully and extract the content from the delta object in the JSON chunks.
Visibility Delay: Since the model is small, add a very short time.sleep() (e.g., 0.01 or 0.02 seconds) between rendering chunks so the streaming effect is visible in the UI.
History Update: Ensure the full final string of the response is appended to st.session_state.messages and saved to the JSON file in the chats/ folder only after the stream is complete.
Error Handling: Ensure the app doesn't hang if the stream is interrupted.
**AI Suggestion:** The AI suggested using response.iter_lines() and a for loop to catch the data: chunks. It provided logic to json.loads() each chunk and pull the text from choices[0].delta.content.
**My Modifications & Reflections:** Code worked as provided.

Task 3: [User Memory]
**Prompt:** I have a multi-turn Streamlit chat app with persistence and streaming. Now, please help me implement Task 3: User Memory with these requirements:
Memory Extraction Logic: After the assistant provides a response, create a second, lightweight API call to meta-llama/Llama-3.2-1B-Instruct.
The Extraction Prompt: Use a system prompt like: 'You are a memory extractor. Given the following conversation, extract key user preferences, traits, or facts (e.g., name, interests, style) and return them ONLY as a valid JSON object. If nothing new is found, return {}.'
JSON Storage: Create a function to save these traits into memory.json. Ensure that new traits are merged with existing ones rather than overwriting the whole file.
Sidebar Display: Add an st.sidebar.expander titled 'User Memory' that displays the current contents of memory.json in a readable format.
Memory Reset: Add a button in the sidebar labeled 'Clear Memory' that wipes the memory.json file and resets the current session's memory.
Personalization: Update the main chat API call to include the stored memory in the 'system'
message. For example: 'You are a helpful assistant. Here is what you know about the user: [Injected Memory].'
Constraints: Ensure the second API call happens in the background and doesn't interrupt the user's experience. Use the requests library.
**AI Suggestion:** The AI suggested a two-step process: first, generating the chat response, then triggering a "hidden" API request to summarize the user's traits. It provided logic for json.load() and json.dump() to manage the memory.json file.
**My Modifications & Reflections:** Code worked as provided.
