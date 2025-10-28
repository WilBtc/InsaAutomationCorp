#!/usr/bin/env python3
"""
Unit tests for dead_letter_queue.py
Tests message storage, retrieval, replay, and analytics
"""
import pytest
import tempfile
import os
import time
import json
from dead_letter_queue import (
    DeadLetterQueue,
    DeadLetter,
    get_dead_letter_queue
)


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    db_path = db_file.name
    db_file.close()
    yield db_path
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def dlq(temp_db):
    """Create a DLQ instance for testing"""
    return DeadLetterQueue(temp_db)


class TestMessageStorage:
    """Test message storage functionality"""

    def test_add_message_with_dict(self, dlq):
        """Test adding a message with dictionary content"""
        message = {"customer_id": "CUST-001", "action": "create_quote"}
        error = ValueError("Invalid customer")

        dlq_id = dlq.add_message(
            topic="quote_generation",
            message=message,
            error=error,
            retry_count=3
        )

        assert dlq_id > 0

        # Verify message was stored
        dead_letter = dlq.get_message_by_id(dlq_id)
        assert dead_letter is not None
        assert dead_letter.topic == "quote_generation"
        assert json.loads(dead_letter.message) == message
        assert dead_letter.error_type == "ValueError"
        assert dead_letter.error_message == "Invalid customer"
        assert dead_letter.retry_count == 3
        assert dead_letter.status == "failed"

    def test_add_message_with_string(self, dlq):
        """Test adding a message with string content"""
        message = "Simple text message"
        error = ConnectionError("Database unavailable")

        dlq_id = dlq.add_message(
            topic="test_topic",
            message=message,
            error=error,
            retry_count=5
        )

        dead_letter = dlq.get_message_by_id(dlq_id)
        assert dead_letter.message == message
        assert dead_letter.error_type == "ConnectionError"

    def test_add_message_with_notes(self, dlq):
        """Test adding a message with notes"""
        dlq_id = dlq.add_message(
            topic="test",
            message="test message",
            error=ValueError("test error"),
            notes="Manual investigation needed"
        )

        dead_letter = dlq.get_message_by_id(dlq_id)
        assert dead_letter.notes == "Manual investigation needed"

    def test_add_message_captures_timestamp(self, dlq):
        """Test that timestamp is captured when adding message"""
        before = time.time()
        dlq_id = dlq.add_message(
            topic="test",
            message="test",
            error=ValueError("test")
        )
        after = time.time()

        dead_letter = dlq.get_message_by_id(dlq_id)
        assert before <= dead_letter.failed_timestamp <= after
        assert dead_letter.original_timestamp > 0


class TestMessageRetrieval:
    """Test message retrieval and filtering"""

    def test_get_failed_messages_returns_all(self, dlq):
        """Test getting all failed messages"""
        # Add multiple messages
        for i in range(5):
            dlq.add_message(
                topic=f"topic_{i}",
                message=f"message_{i}",
                error=ValueError(f"error_{i}")
            )

        messages = dlq.get_failed_messages()
        assert len(messages) == 5

    def test_get_failed_messages_filter_by_topic(self, dlq):
        """Test filtering messages by topic"""
        dlq.add_message(topic="topic_a", message="msg1", error=ValueError("err1"))
        dlq.add_message(topic="topic_b", message="msg2", error=ValueError("err2"))
        dlq.add_message(topic="topic_a", message="msg3", error=ValueError("err3"))

        messages = dlq.get_failed_messages(topic="topic_a")
        assert len(messages) == 2
        assert all(m.topic == "topic_a" for m in messages)

    def test_get_failed_messages_filter_by_error_type(self, dlq):
        """Test filtering messages by error type"""
        dlq.add_message(topic="test", message="msg1", error=ValueError("err1"))
        dlq.add_message(topic="test", message="msg2", error=ConnectionError("err2"))
        dlq.add_message(topic="test", message="msg3", error=ValueError("err3"))

        messages = dlq.get_failed_messages(error_type="ValueError")
        assert len(messages) == 2
        assert all(m.error_type == "ValueError" for m in messages)

    def test_get_failed_messages_filter_by_status(self, dlq):
        """Test filtering messages by status"""
        dlq_id = dlq.add_message(topic="test", message="msg1", error=ValueError("err1"))
        dlq.add_message(topic="test", message="msg2", error=ValueError("err2"))

        # Mark one as replayed
        dlq._mark_replayed(dlq_id)

        failed = dlq.get_failed_messages(status="failed")
        replayed = dlq.get_failed_messages(status="replayed")

        assert len(failed) == 1
        assert len(replayed) == 1

    def test_get_failed_messages_respects_limit(self, dlq):
        """Test that limit parameter works"""
        for i in range(10):
            dlq.add_message(topic="test", message=f"msg_{i}", error=ValueError("err"))

        messages = dlq.get_failed_messages(limit=5)
        assert len(messages) == 5

    def test_get_failed_messages_respects_offset(self, dlq):
        """Test that offset parameter works for pagination"""
        for i in range(10):
            dlq.add_message(topic="test", message=f"msg_{i}", error=ValueError("err"))

        page1 = dlq.get_failed_messages(limit=3, offset=0)
        page2 = dlq.get_failed_messages(limit=3, offset=3)

        assert len(page1) == 3
        assert len(page2) == 3
        # Messages should be different (ordered by timestamp DESC)
        assert page1[0].id != page2[0].id

    def test_get_message_by_id_returns_none_if_not_found(self, dlq):
        """Test that getting non-existent message returns None"""
        message = dlq.get_message_by_id(999999)
        assert message is None


class TestMessageReplay:
    """Test message replay functionality"""

    def test_replay_message_success(self, dlq):
        """Test successful message replay"""
        message = {"customer_id": "CUST-001"}
        dlq_id = dlq.add_message(
            topic="test_topic",
            message=message,
            error=ValueError("test error")
        )

        replayed_messages = []

        def replay_callback(topic, msg):
            replayed_messages.append((topic, msg))

        success = dlq.replay_message(dlq_id, replay_callback)

        assert success is True
        assert len(replayed_messages) == 1
        assert replayed_messages[0][0] == "test_topic"
        assert replayed_messages[0][1] == message

        # Verify message is marked as replayed
        dead_letter = dlq.get_message_by_id(dlq_id)
        assert dead_letter.status == "replayed"
        assert dead_letter.replayed_at is not None

    def test_replay_nonexistent_message_fails(self, dlq):
        """Test replaying non-existent message fails"""
        def replay_callback(topic, msg):
            pass

        success = dlq.replay_message(999999, replay_callback)
        assert success is False

    def test_replay_already_replayed_message_fails(self, dlq):
        """Test replaying already-replayed message fails"""
        dlq_id = dlq.add_message(topic="test", message="msg", error=ValueError("err"))

        def replay_callback(topic, msg):
            pass

        # First replay should succeed
        assert dlq.replay_message(dlq_id, replay_callback) is True

        # Second replay should fail
        assert dlq.replay_message(dlq_id, replay_callback) is False

    def test_replay_message_handles_callback_failure(self, dlq):
        """Test replay failure when callback raises exception"""
        dlq_id = dlq.add_message(topic="test", message="msg", error=ValueError("err"))

        def failing_callback(topic, msg):
            raise RuntimeError("Callback failed")

        success = dlq.replay_message(dlq_id, failing_callback)
        assert success is False

        # Message should still be in 'failed' state
        dead_letter = dlq.get_message_by_id(dlq_id)
        assert dead_letter.status == "failed"


class TestStatistics:
    """Test statistics and analytics"""

    def test_get_statistics_empty_queue(self, dlq):
        """Test statistics on empty queue"""
        stats = dlq.get_statistics()

        assert stats['total_messages'] == 0
        assert stats['by_status'] == {}
        assert stats['by_topic'] == {}
        assert stats['by_error_type'] == {}
        assert stats['oldest_message'] is None
        assert stats['newest_message'] is None

    def test_get_statistics_with_messages(self, dlq):
        """Test statistics with messages"""
        # Add various messages
        dlq.add_message(topic="topic_a", message="msg1", error=ValueError("err1"))
        dlq.add_message(topic="topic_a", message="msg2", error=ValueError("err2"))
        dlq.add_message(topic="topic_b", message="msg3", error=ConnectionError("err3"))

        stats = dlq.get_statistics()

        assert stats['total_messages'] == 3
        assert stats['by_status']['failed'] == 3
        assert stats['by_topic']['topic_a'] == 2
        assert stats['by_topic']['topic_b'] == 1
        assert stats['by_error_type']['ValueError'] == 2
        assert stats['by_error_type']['ConnectionError'] == 1
        assert stats['oldest_message'] is not None
        assert stats['newest_message'] is not None

    def test_get_statistics_tracks_status_changes(self, dlq):
        """Test that statistics track status changes"""
        dlq_id1 = dlq.add_message(topic="test", message="msg1", error=ValueError("err1"))
        dlq_id2 = dlq.add_message(topic="test", message="msg2", error=ValueError("err2"))

        # Mark one as replayed
        dlq._mark_replayed(dlq_id1)

        stats = dlq.get_statistics()
        assert stats['by_status']['failed'] == 1
        assert stats['by_status']['replayed'] == 1


class TestRetentionPolicy:
    """Test retention policy and cleanup"""

    def test_delete_old_messages(self, dlq):
        """Test deleting old messages"""
        # Add messages with different timestamps
        old_time = time.time() - (40 * 24 * 60 * 60)  # 40 days ago

        # Add old message
        dlq_id1 = dlq.add_message(topic="test", message="old_msg", error=ValueError("err"))
        # Manually update timestamp to make it old
        import sqlite3
        with sqlite3.connect(dlq.db_path) as conn:
            conn.execute("UPDATE dead_letters SET failed_timestamp = ? WHERE id = ?", (old_time, dlq_id1))
            conn.commit()

        # Mark as replayed
        dlq._mark_replayed(dlq_id1)

        # Add recent message
        dlq_id2 = dlq.add_message(topic="test", message="new_msg", error=ValueError("err"))

        # Delete messages older than 30 days with status 'replayed'
        deleted = dlq.delete_old_messages(days=30, status="replayed")

        assert deleted == 1

        # Verify old message is deleted
        assert dlq.get_message_by_id(dlq_id1) is None

        # Verify recent message is not deleted
        assert dlq.get_message_by_id(dlq_id2) is not None

    def test_delete_old_messages_respects_status(self, dlq):
        """Test that deletion respects status filter"""
        old_time = time.time() - (40 * 24 * 60 * 60)

        dlq_id = dlq.add_message(topic="test", message="msg", error=ValueError("err"))

        # Make it old
        import sqlite3
        with sqlite3.connect(dlq.db_path) as conn:
            conn.execute("UPDATE dead_letters SET failed_timestamp = ? WHERE id = ?", (old_time, dlq_id))
            conn.commit()

        # Don't mark as replayed (status is 'failed')

        # Try to delete 'replayed' messages
        deleted = dlq.delete_old_messages(days=30, status="replayed")

        assert deleted == 0
        assert dlq.get_message_by_id(dlq_id) is not None


class TestUpdateNotes:
    """Test updating message notes"""

    def test_update_notes(self, dlq):
        """Test updating notes for a message"""
        dlq_id = dlq.add_message(
            topic="test",
            message="msg",
            error=ValueError("err"),
            notes="Initial note"
        )

        dlq.update_notes(dlq_id, "Updated note with investigation results")

        dead_letter = dlq.get_message_by_id(dlq_id)
        assert dead_letter.notes == "Updated note with investigation results"


class TestGlobalInstance:
    """Test global instance management"""

    def test_get_dead_letter_queue_returns_singleton(self, temp_db):
        """Test that get_dead_letter_queue returns same instance"""
        dlq1 = get_dead_letter_queue(temp_db)
        dlq2 = get_dead_letter_queue(temp_db)

        assert dlq1 is dlq2


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])
