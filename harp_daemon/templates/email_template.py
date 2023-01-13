template = """
<!DOCTYPE html
    PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en-GB">
​
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <title>Harp</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
​
    <style type="text/css">
        a[x-apple-data-detectors] {
            color: inherit !important;
        }
    </style>
​
</head>
​
<body style="margin: 0; padding: 0; background: #ECF0F7;">
    <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
        <tr>
            <td style="padding: 80px 0 30px 0;">
​
                <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%"
                    style="border-collapse: collapse;max-width: 600px">
                    <tr>
                        <td bgcolor="#ffffff" style="padding: 40px; border-radius: 0 0 12px 12px;">
                            <table border="0" cellpadding="0" cellspacing="0" width="100%"
                                style="border-collapse: collapse;">
                                <tr>
                                    <td style="border-radius: 12px; color: #153643; font-family: Arial, sans-serif; background: #F4F8FC; padding: 30px; font-size: 16px; text-align: center; line-height: 24px;">
                                        {email_body}
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
​
                </table>
​
            </td>
        </tr>
    </table>
</body>
​
</html>
"""