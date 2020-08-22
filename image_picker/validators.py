from django.core.exceptions import ValidationError
from pathlib import Path


def validate_path_exists(value):
	
	if not Path(value).exists():
		raise ValidationError(
			"Given path doesn't exists"
		)


def validate_is_dir(value):
	if not Path(value).is_dir():
		raise ValidationError(
			"Given path is not a directory"
		)
