from models.user import User


class TestUserModel:
    def test_add_and_get_users(self):
        User.add_user("admin", "pass", "Admin")
        User.add_user("ceo", "pass", "CEO")
        users = User.get_all_users()
        assert len(users) >= 2
        usernames = {u.username for u in users}
        assert "admin" in usernames
        assert "ceo" in usernames

    def test_update_user_by_username(self):
        User.add_user("manager", "pass", "Manager")
        assert User.authenticate("manager", "pass") is not None
        User.update_user("manager", "manager2", "newpass", "Manager")
        assert User.authenticate("manager", "pass") is None
        assert User.authenticate("manager2", "newpass") is not None

    def test_authenticate_success_and_failure(self):
        User.add_user("user1", "secret", "Manager")
        assert User.authenticate("user1", "secret") is not None
        assert User.authenticate("user1", "wrong") is None
        assert User.authenticate("ghost", "secret") is None

    def test_delete_user(self):
        User.add_user("temp", "pass", "Staff")
        assert User.authenticate("temp", "pass") is not None
        User.delete_user("temp")
        assert User.authenticate("temp", "pass") is None
