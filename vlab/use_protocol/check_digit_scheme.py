class Algoritme:
    @staticmethod
    def __only_digest(text: str):
        if text.isdigit(): raise ValueError("The text's digit must be numeric")

    @staticmethod
    def m10(text: str) -> str:
        Algoritme.__only_digest(text)
        
        total = 0

        reverse_digits = [int(digit) for digit in reversed(text)]

        for idx, digit in enumerate(reverse_digits):
            if idx % 2 == 0:
                doubled = digit * 2
                total += doubled if doubled < 10 else (doubled - 9)
            else:
                total += digit

        remainder = total % 10
        check_digit = (10 - remainder) % 10
        return str(check_digit)

    @staticmethod
    def m11(text: str) -> str:
        Algoritme.__only_digest(text)
        
        total  = 0
        weight = 2

        for digit in reversed(text):
            total = int(digit) * weight
            weight += 1
            if weight > 9:
                weight = 2

        remainder = total % 11
        diference = 11 - remainder
        if diference in [10, 11]:
            return '0'

        return str(diference)

    
    @staticmethod
    def iso(text: str) -> str:
        '''ISO 7064 Mod 11, 10'''

        Algoritme.__only_digest(text)

        p = 10

        for char in text:
            digit = int(char)
            s = (p + digit) % 10
            if s == 0:
                s = 10
            p = (s * 2) % 11

        check_digit = (11 - p) % 10
        return str(check_digit)

    @staticmethod
    def npi(text: str) -> str:
        Algoritme.__only_digest(text)
        
        if not len(text) == 9:
            raise ValueError("The NPI's base ID must contain exatily 9 digit")

        full_string = '80840' + text
        total = 0
        reverse_digits = [int(digit) for digit in reversed(full_string)]

        for idx, digit in enumerate(reverse_digits):
            if idx % 2 == 0:
                doubled = digit * 2
                total += doubled if doubled < 10 else (doubled - 9)
            else:
                total += digit

        remainder = total % 10
        check_digit = (10 - remainder) % 10
        return str(check_digit)

    @staticmethod
    def bc39(text: str) -> str:
        CHARSET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-. $/+%"
        total = 0

        for char in text.upper():
            if char in CHARSET:
                total += CHARSET.index(char)
            else:
                raise ValueError(f'Charachter invalid for code 39: {char}')

        remainder = total % 43
        return CHARSET[remainder]

    @staticmethod
    def bc93(text: str) -> str:
        CHARSET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-. $/+%$"

        total_c = 0
        weight  = 1

        for char in reversed(text.upper()):
            if char not in CHARSET:
                raise ValueError(f'Charachter invalid for code 93: {char}')
            
            total_c += CHARSET.index(char) * weight
            weight += 1
            if weight > 20:
                weight = 1

        check_digit_c = CHARSET[total_c % 47]

        text_with_c = text.upper() + check_digit_c
        total_k = 0
        weight = 1

        for char in reversed(text_with_c):
            total_k += CHARSET.index(char) * weight
            weight += 1
            if weight > 15:
                weight = 1

        check_digit_k = CHARSET[total_k % 47]

        return check_digit_c + check_digit_k

    @staticmethod
    def oth(text: str):
        Algoritme.__only_digest(text)

        total = 0
        for idx, digit in enumerate(reversed(text)):
            multiplier = 3 if idx % 2 == 0 else 1
            total += int(digit) * multiplier

        remainder = total % 10
        check_digit = (10 - remainder) % 10
        return str(check_digit)
