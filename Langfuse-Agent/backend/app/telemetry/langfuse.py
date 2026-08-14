from langfuse import get_client

langfuse = get_client()


def get_trace_url():
    trace_id = langfuse.get_current_trace_id()

    if not trace_id:
        return None

    return langfuse.get_trace_url(trace_id=trace_id)