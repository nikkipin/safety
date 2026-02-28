import base64
import json

from urllib.parse import urlsplit, urlunsplit

from safety.tool.constants import (
    NPMJS_PUBLIC_REPOSITORY_URL,
    PYPI_PUBLIC_REPOSITORY_URL,
)
from typing import TYPE_CHECKING, Optional, Literal

if TYPE_CHECKING:
    from safety.auth.models import Auth
    from safety.cli_util import CustomContext
    from safety.models import SafetyCLI

    SafetyContext = CustomContext[SafetyCLI]


def index_credentials(ctx: "SafetyContext") -> str:
    """
    Returns the index credentials for the current context.
    This should be used together with user:index_credential for index
    basic auth.

    Args:
        ctx (SafetyContext): The context.

    Returns:
        str: The index credentials.
    """
    api_key = None
    token = None
    machine_id = None
    machine_token = None

    auth_obj = getattr(ctx.obj, "auth", None)

    if auth_obj is not None:
        auth: "Auth" = auth_obj

        client = auth.platform
        # Machine token takes priority for envelope construction. In practice
        # machine_token and api_key are not expected together (the Auth setup
        # provides a single auth method), but __init__ only validates the
        # machine_id/machine_token pairing — not api_key exclusivity.
        if client.has_machine_token:
            machine_id = client.machine_id
            machine_token = client.get_machine_token_for_firewall()
        else:
            token = client.token.get("access_token") if client.token else None
            api_key = client.api_key

    if machine_id and machine_token:
        auth_envelop = json.dumps(
            {
                "version": "2.0",
                "machine_id": machine_id,
                "machine_token": machine_token,
                "project_id": ctx.obj.project.id if ctx.obj.project else None,
            }
        )
    else:
        auth_envelop = json.dumps(
            {
                "version": "1.0",
                "access_token": token,
                "api_key": api_key,
                "project_id": ctx.obj.project.id if ctx.obj.project else None,
            }
        )
    return base64.urlsafe_b64encode(auth_envelop.encode("utf-8")).decode("utf-8")


def build_index_url(
    ctx: "SafetyContext", index_url: Optional[str], index_type: Literal["pypi", "npm"]
) -> str:
    """
    Builds the index URL for the current context.
    """
    if index_url is None:
        # TODO: Make this to select the index based on auth org or project
        index_url = {
            "pypi": PYPI_PUBLIC_REPOSITORY_URL,
            "npm": NPMJS_PUBLIC_REPOSITORY_URL,
        }[index_type]

    url = urlsplit(index_url)

    encoded_auth = index_credentials(ctx)
    netloc = f"user:{encoded_auth}@{url.netloc}"

    if type(url.netloc) is bytes:
        url = url._replace(netloc=netloc.encode("utf-8"))
    elif type(url.netloc) is str:
        url = url._replace(netloc=netloc)

    return urlunsplit(url)
