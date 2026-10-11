"""A queue holding more than one waiting case is a warning."""

from underwriting.queues import MessageQueue


def test_second_waiting_message_warns() -> None:
    queue = MessageQueue("application_received")
    assert queue.put({"applicant_id": "APP-1"}) is None
    warning = queue.put({"applicant_id": "APP-2"})
    assert warning == "application_received depth is 2"
    assert queue.depth() == 2
