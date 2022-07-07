cron_d "staging-pycon-account-expunge" do
  hour "0"
  minute "0"
  command "bash -c 'source /srv/staging-pycon.python.org/shared/.env && cd /srv/staging-pycon.python.org/current && /srv/staging-pycon.python.org/shared/env/bin/python manage.py expunge_deleted'"
end

cron_d "staging-pycon-update-tutorial-registrants" do
  hour "0"
  minute "20"
  command "bash -c 'source /srv/staging-pycon.python.org/shared/.env && cd /srv/staging-pycon.python.org/current && /srv/staging-pycon.python.org/shared/env/bin/python manage.py update_tutorial_registrants'"
end