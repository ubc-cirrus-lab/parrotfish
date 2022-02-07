from spot.invocation.aws_credentials_fetch import AWSCredentialsFetch


def test_credentials():
    creds = AWSCredentialsFetch()
    assert len(creds._fields) == 2
    assert creds.get_access_key_id != ""
    assert creds.get_secret_access_key != ""
    # Use the paramter -s in pytest to print the keys to confirm match if necessary
    print(creds.get_secret_access_key())
    print(creds.get_access_key_id())
