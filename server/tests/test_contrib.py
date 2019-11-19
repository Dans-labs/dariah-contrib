def test_add(client):
    """Can an unauthenticated user insert into the contrib table?"""
    response = client.get(f"/api/contrib/insert")
