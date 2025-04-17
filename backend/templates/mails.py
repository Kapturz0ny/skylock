def two_fa_code_mail(username: str, token_code: int, token_life: int) -> str:
	"""
	Generates an HTML email template for sending a 2FA code to the user.

	Args:
		username (str): The username of the user.
		token_code (int): The 2FA token code.
		token_life (int): The lifetime of the token in seconds.

	Returns:
		str: The HTML email template as a string.
	"""
	return f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h2>Hello {username}!</h2>
            <p>
            Thank you for registering with Skylock.
            Please use the following <strong>2FA token</strong> to complete your registration:
            </p>
            <p style="font-size: 1.2em; font-weight: bold; color: #2E86C1;">
            {token_code}
            </p>
            <p>
            Please note that the code will expire in {token_life / 60} minutes
            If you did not initiate this request, please disregard this email.
            </p>
            <p>
            Best regards,<br>
            The Skylock Team
            </p>
        </body>
        </html>
		"""