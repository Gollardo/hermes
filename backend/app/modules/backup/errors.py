class InvalidHermesFile(ValueError):
    pass


class UnsupportedHermesVersion(ValueError):
    pass


class InvalidKdfParameters(ValueError):
    pass


class BackupAuthenticationFailed(ValueError):
    pass


class InvalidBackupPayload(ValueError):
    pass


class BackupTooLarge(ValueError):
    pass
