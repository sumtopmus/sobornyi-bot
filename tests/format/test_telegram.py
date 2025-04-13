import pytest

from format import mention, replace_brackets


class TestMention:
    def test_mention_with_username(self, mock_user):
        # Set up the mock to match the actual implementation
        name_mention = f"[{mock_user.name}](tg://user?id={mock_user.id})"
        username_mention = f"[@{mock_user.username}](https://t.me/{mock_user.username})"

        # First call with name, second call without args
        mock_user.mention_markdown.side_effect = [name_mention, username_mention]

        result = mention(mock_user)

        # The user has a username, so both mentions should be included
        assert name_mention in result
        assert f"({username_mention})" in result

    def test_mention_without_username(self, mock_user):
        mock_user.username = None
        name_mention = f"[{mock_user.name}](tg://user?id={mock_user.id})"
        mock_user.mention_markdown.return_value = name_mention

        result = mention(mock_user)

        # Only the name mention should be included
        assert result == name_mention


@pytest.mark.parametrize(
    "input_text,expected",
    [
        ("", ""),
        ("hello world", "hello world"),
        ("[test]", "(test)"),
        ("[one] [two] [three]", "(one) (two) (three)"),
        (
            "text [with] some (existing) brackets",
            "text (with) some (existing) brackets",
        ),
    ],
)
def test_replace_brackets(input_text: str, expected: str):
    assert replace_brackets(input_text) == expected
