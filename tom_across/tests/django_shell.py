#!/usr/bin/env python
# django_shell.py

from django.core.management import call_command
from tom_across.tests.boot_django import boot_django

boot_django()
call_command('shell_plus')
