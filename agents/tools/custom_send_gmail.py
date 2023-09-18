from langchain.tools.gmail import GmailSendMessage


"""Send Gmail messages."""
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional, Union
from email.mime.base import MIMEBase

from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools.gmail.base import GmailBaseTool

import io

def read_local_file(file_path):
    """Reads a local file and returns a BytesIO object."""
    with open(file_path, 'rb') as f:
        file_data = io.BytesIO(f.read())
    return file_data

class SendMessageSchema(BaseModel):
    """Input for SendMessageTool."""

    message: str = Field(
        ...,
        description="The message to send.",
    )
    to: Union[str, List[str]] = Field(
        ...,
        description="The list of recipients.",
    )
    subject: str = Field(
        ...,
        description="The subject of the message.",
    )
    cc: Optional[Union[str, List[str]]] = Field(
        None,
        description="The list of CC recipients.",
    )
    bcc: Optional[Union[str, List[str]]] = Field(
        None,
        description="The list of BCC recipients.",
    )
    # attachment: Optional[Union[str, List[str]]] = Field(
    #     None,
    #     description="The list of attached files.",
    # )
    # attachment_id: Optional[Union[str, List[str]]] = Field(
    #     None,
    #     description="The list of attached files.",
    # )
    attachment_path: Optional[str] = Field(
        None,
        description="List of Path to the file to be attached.",
    )
    attachment_name: Optional[str] = Field(
        None,
        description="Name of the attached file.",
    )


class GmailSendMessageWithAttachment(GmailBaseTool):
    """Tool that sends a message to Gmail."""

    name: str = "send_gmail_message"
    description: str = (
        "Use this tool to send email messages." " The input is the message, recipients"
    )



    def _prepare_message(
        self,
        message: str,
        to: Union[str, List[str]],
        subject: str,
        cc: Optional[Union[str, List[str]]] = None,
        bcc: Optional[Union[str, List[str]]] = None,
        attachment_id: Optional[str] = None,
        attachment_name: Optional[str] = "attachment"
    ) -> Dict[str, Any]:
        """Create a message for an email."""
        mime_message = MIMEMultipart()
        mime_message.attach(MIMEText(message, "html"))

        mime_message["To"] = ", ".join(to if isinstance(to, list) else [to])
        mime_message["Subject"] = subject

        if cc is not None:
            mime_message["Cc"] = ", ".join(cc if isinstance(cc, list) else [cc])
        if bcc is not None:
            mime_message["Bcc"] = ", ".join(bcc if isinstance(bcc, list) else [bcc])

        if attachment_id:  # Use a local path instead of Google Drive file ID
            file_data = read_local_file(attachment_id)
            attachment = MIMEBase('application', 'octet-stream')
            attachment.set_payload(file_data.read())
            attachment.add_header('Content-Disposition', 'attachment', filename=attachment_name)
            mime_message.attach(attachment)


        encoded_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()
        return {"raw": encoded_message}


    def _run(
        self,
        message: str,
        to: Union[str, List[str]],
        subject: str,
        cc: Optional[Union[str, List[str]]] = None,
        bcc: Optional[Union[str, List[str]]] = None,
        attachment_id: Optional[str] = None,
        attachment_name: Optional[str] = "attachment",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Run the tool."""
        try:
            create_message = self._prepare_message(
                message, to, subject, cc=cc, bcc=bcc, 
                attachment_id=attachment_id, attachment_name=attachment_name
            )
            send_message = (
                self.api_resource.users()
                .messages()
                .send(userId="me", body=create_message)
            )
            sent_message = send_message.execute()
            return f'Message sent. Message Id: {sent_message["id"]}'
        except Exception as error:
            raise Exception(f"An error occurred: {error}")


