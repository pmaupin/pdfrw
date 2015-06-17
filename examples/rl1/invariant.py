import reportlab.rl_settings

# Keep reportlab from changing the date on us,
# so that we can get a fix on the MD5.

reportlab.rl_settings.invariant = True
