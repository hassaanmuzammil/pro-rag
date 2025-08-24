import ast
import base64
import chainlit as cl
import chainlit.data as cl_data
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
from sqlalchemy import select

from src.builder import pipeline
from src.config import CHAINLIT_DB_URL
from src.db.session import AsyncSessionFactory
from src.db.models import UploadedFile

conninfo = f"postgresql+asyncpg://{CHAINLIT_DB_URL}"
cl_data._data_layer = SQLAlchemyDataLayer(conninfo=conninfo, ssl_require=False)

@cl.set_starters
async def set_starters():
    return []

@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("history", [])
    cl.user_session.set("pipeline", pipeline)
    cl.user_session.set("processor", pipeline.processor)
    actions = [
        cl.Action(
            name="get_files_action",
            payload={},
            label="Get Files",
            icon="file-text"
        ),
        cl.Action(
            name="upload_file_action",
            payload={},
            label="Upload File",
            icon="upload"
        ),
        cl.Action(
            name="delete_file_action",
            payload={},
            label="Delete File",
            icon="trash-2"
        )
    ]
    await cl.Message(
        content="## File Management Options",
        actions=actions
    ).send()

@cl.password_auth_callback
def auth_callback(username: str, password: str):
    if (username, password) == ("admin", "admin"):
        user = cl.User(identifier="admin", display_name="Admin User", metadata={})
    else:
        user = None
    return user

@cl.on_stop
def on_stop():
    cl.user_session.set("stop", True)

@cl.on_message
async def on_message(message: cl.Message):
    history = cl.user_session.get("history")
    pipeline = cl.user_session.get("pipeline")
    processor = cl.user_session.get("processor")    
    chat_history = "\n".join(f"{item['role'].capitalize()}: {item['content']}" for item in history[-5:])
    user_message = message.content
    history.append(
        {
            "role": "user",
            "content": user_message
        }
    )
    rewritten_query = ""
    async with cl.Step("Query Rewrite") as step:
        rewritten_query, fallback_message = await processor.query_rewrite(
            chat_history=chat_history,
            message=user_message
        )
        step.output = rewritten_query if rewritten_query else "Not applicable"

    if not rewritten_query:
        res = fallback_message
        response = cl.Message(content=res)
        await response.send()
    else:
        cl.user_session.set("stop", False)
        sources = await pipeline.retrieve(rewritten_query, expand_context=False)
        context = processor.build_context(sources)
        stream = processor.final_answer(message=rewritten_query, context=context)
        response = cl.Message(content="")
        res = ""
        async for chunk in stream:
            if cl.user_session.get("stop"):
                break
            res += chunk
            await response.stream_token(chunk)
        elements = []
        names = []
        for source in sources:
            name = f"Source: {source.get('name')} (page {source.get('page')})"
            content = source.get("content")
            names.append(name)
            element = cl.Text(
                content=content, name=name, display="side"
            )
            elements.append(element)
        names = "\n".join(names)
        result = f"{res}\n\nSources:\n{names}"
        response.content = result
        response.elements = elements
        await response.update()
        await response.send()

    history.append(
        {
            "role": "assistant",
            "content": res
        }
    )
    cl.user_session.set("history", history)

@cl.on_chat_end
def end():
    pass

@cl.action_callback("get_files_action")
async def get_files_action(action: cl.Action):
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(UploadedFile))
        files = result.scalars().all()
    props = {"files": [f.filename for f in files]}
    file_element = cl.CustomElement(name="GetFiles", props=props)
    await cl.Message(
        content="Here is the files information!",
        elements=[file_element]
    ).send()

@cl.action_callback("delete_file_action")
async def delete_file_action(action: cl.Action):
    element = cl.CustomElement(name="DeleteFileModal", props={"filename": ""})
    await cl.Message(
        content="Enter the filename to delete:",
        elements=[element]
    ).send()

@cl.action_callback("confirm_delete_file")
async def confirm_delete_file(action: cl.Action):
    filename = action.payload.get("filename")
    if filename:
        # TODO: Implement delete file logic (use `delete_file` from src.api.file)
        await cl.Message(content=f"Deleted file: {filename}").send()
    else:
        await cl.Message(content="No filename provided.").send()

@cl.action_callback("upload_file_action")
async def upload_file_action(action: cl.Action):
    element = cl.CustomElement(name="UploadFileModal", props={})
    await cl.Message(
        content="Select a file to upload:",
        elements=[element]
    ).send()

@cl.action_callback("confirm_upload_file")
async def confirm_upload_file(action: cl.Action):
    filename = action.payload.get("filename")
    file_data = action.payload.get("file")
    if filename and file_data:
        # Decode the base64 to bytes
        content = base64.b64decode(file_data.split(",")[1])
        size_kb = len(content) / 1024  # size in KB
        # TODO: Implement file upload logic (use `upload_file` from src.api.file)
        await cl.Message(
            content=f"File '{filename}' uploaded successfully ({size_kb:.2f} KB)"
        ).send()
    else:
        await cl.Message(content="No file selected.").send()


if __name__ == "__main__":

    from chainlit.cli import run_chainlit
    run_chainlit(__file__)