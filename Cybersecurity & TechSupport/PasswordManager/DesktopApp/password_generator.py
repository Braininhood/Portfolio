#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Password Generator - Generates secure passwords with configurable options.
"""

import random
import string
import re

class PasswordGenerator:
    """Generates secure random passwords"""
    
    def __init__(self):
        """Initialize the password generator"""
        self.char_sets = {
            'lowercase': string.ascii_lowercase,
            'uppercase': string.ascii_uppercase,
            'numbers': string.digits,
            'symbols': '!@#$%^&*()_+-=[]{}|;:,.<>?'
        }
        
        self.default_options = {
            'length': 16,
            'include_lowercase': True,
            'include_uppercase': True,
            'include_numbers': True,
            'include_symbols': True,
            'exclude_similar_chars': False,
            'exclude_ambiguous': False,
            'require_all_char_types': True
        }
    
    def generate(self, options=None):
        """Generate a secure random password based on provided options
        
        Args:
            options (dict, optional): Password generation options
            
        Returns:
            str: Generated password
        """
        # Merge provided options with defaults
        opts = self.default_options.copy()
        if options:
            opts.update(options)
        
        # Validate input
        if opts['length'] < 4 and opts['require_all_char_types']:
            raise ValueError("Password length must be at least 4 when requiring all character types")
        
        if opts['length'] < 1:
            raise ValueError("Password length must be at least 1")
        
        # Build character pool based on options
        char_pool = ''
        selected_char_sets = []
        
        if opts['include_lowercase']:
            chars = self.char_sets['lowercase']
            if opts['exclude_similar_chars']:
                chars = chars.replace('l', '').replace('i', '').replace('o', '')
            char_pool += chars
            selected_char_sets.append(chars)
        
        if opts['include_uppercase']:
            chars = self.char_sets['uppercase']
            if opts['exclude_similar_chars']:
                chars = chars.replace('I', '').replace('O', '')
            char_pool += chars
            selected_char_sets.append(chars)
        
        if opts['include_numbers']:
            chars = self.char_sets['numbers']
            if opts['exclude_similar_chars']:
                chars = chars.replace('0', '').replace('1', '')
            char_pool += chars
            selected_char_sets.append(chars)
        
        if opts['include_symbols']:
            chars = self.char_sets['symbols']
            if opts['exclude_ambiguous']:
                chars = chars.replace('\\', '').replace('`', '').replace('~', '').replace('\'', '').replace('"', '')
            char_pool += chars
            selected_char_sets.append(chars)
        
        # Ensure we have at least one character type
        if not char_pool:
            raise ValueError("At least one character type must be selected")
        
        # Generate password
        if opts['require_all_char_types'] and selected_char_sets:
            return self._generate_with_required_sets(opts['length'], selected_char_sets)
        else:
            return self._generate_random(opts['length'], char_pool)
    
    def _generate_random(self, length, char_pool):
        """Generate a random password from a character pool
        
        Args:
            length (int): Password length
            char_pool (str): Pool of characters to use
            
        Returns:
            str: Generated password
        """
        return ''.join(random.choice(char_pool) for _ in range(length))
    
    def _generate_with_required_sets(self, length, char_sets):
        """Generate a password ensuring each character set is used at least once
        
        Args:
            length (int): Password length
            char_sets (list): Character sets to include
            
        Returns:
            str: Generated password
        """
        if length < len(char_sets):
            raise ValueError(f"Password length must be at least {len(char_sets)} to include all character types")
        
        # First, include at least one character from each set
        password_chars = []
        
        # Choose one random character from each required set
        for char_set in char_sets:
            password_chars.append(random.choice(char_set))
        
        # Fill the rest with random characters from all sets
        all_chars = ''.join(char_sets)
        for _ in range(length - len(char_sets)):
            password_chars.append(random.choice(all_chars))
        
        # Shuffle the characters to randomize positions
        random.shuffle(password_chars)
        
        return ''.join(password_chars)
    
    def analyze_strength(self, password):
        """Analyze a password's strength
        
        Args:
            password (str): Password to analyze
            
        Returns:
            dict: Analysis results with score and feedback
        """
        if not password:
            return {
                'score': 0, 
                'strength': 'Very Weak',
                'feedback': 'No password provided'
            }
        
        # Calculate base score from length (up to 40 points)
        length = len(password)
        score = min(40, length * 2.5)
        
        # Check for character variety
        has_lower = bool(re.search(r'[a-z]', password))
        has_upper = bool(re.search(r'[A-Z]', password))
        has_number = bool(re.search(r'\d', password))
        has_symbol = bool(re.search(r'[^a-zA-Z0-9]', password))
        
        # Award points for character variety (up to 20 points)
        score += (has_lower * 5)
        score += (has_upper * 5)
        score += (has_number * 5)
        score += (has_symbol * 5)
        
        # Penalty for repeating patterns (up to -20 points)
        repeats = re.findall(r'(.)\1+', password)
        repeat_penalty = sum((len(match) - 1) * 2 for match in repeats)
        score -= min(20, repeat_penalty)
        
        # Check for sequences
        sequences = [
            'abcdefghijklmnopqrstuvwxyz',
            '01234567890',
            'qwertyuiop',
            'asdfghjkl',
            'zxcvbnm'
        ]
        
        sequence_penalty = 0
        lowercase_password = password.lower()
        
        for seq in sequences:
            for i in range(len(seq) - 2):
                pattern = seq[i:i+3]
                if pattern in lowercase_password:
                    sequence_penalty += 5
        
        score -= min(20, sequence_penalty)
        
        # Normalize score to 0-100 range
        score = max(0, min(100, score))
        
        # Determine strength category and feedback
        if score < 20:
            strength = 'Very Weak'
            feedback = 'This password is extremely vulnerable. Consider using the password generator.'
        elif score < 40:
            strength = 'Weak'
            feedback = 'This password is too simple. Add more length and variety.'
        elif score < 60:
            strength = 'Moderate'
            feedback = 'This password provides some protection but could be stronger.'
        elif score < 80:
            strength = 'Strong'
            feedback = 'This is a good password with a mix of characters.'
        else:
            strength = 'Very Strong'
            feedback = 'Excellent password with great length and complexity.'
        
        return {
            'score': score,
            'strength': strength,
            'feedback': feedback,
            'has_lower': has_lower,
            'has_upper': has_upper,
            'has_number': has_number,
            'has_symbol': has_symbol,
            'length': length
        }
    
    def estimate_crack_time(self, password):
        """Calculate estimated time to crack a password based on its strength
        
        Args:
            password (str): Password to analyze
            
        Returns:
            dict: Time estimates for different attack scenarios
        """
        if not password:
            return {'online': 'Instant', 'offline': 'Instant'}
        
        # Character set size estimation
        charset_size = 0
        if re.search(r'[a-z]', password): charset_size += 26
        if re.search(r'[A-Z]', password): charset_size += 26
        if re.search(r'[0-9]', password): charset_size += 10
        if re.search(r'[^a-zA-Z0-9]', password): charset_size += 33
        
        if charset_size == 0:
            charset_size = 26  # Default if no recognizable chars
        
        # Calculate total possible combinations
        combinations = charset_size ** len(password)
        
        # Estimated attempts per second
        online_attack_speed = 10  # 10 attempts per second for online attack
        offline_attack_speed = 10_000_000_000  # 10 billion per second for offline attack
        
        online_seconds = combinations / online_attack_speed
        offline_seconds = combinations / offline_attack_speed
        
        return {
            'online': self._format_time_estimate(online_seconds),
            'offline': self._format_time_estimate(offline_seconds)
        }
    
    def _format_time_estimate(self, seconds):
        """Format a time estimate in a human-readable way
        
        Args:
            seconds (float): Time in seconds
            
        Returns:
            str: Formatted time string
        """
        if seconds < 1:
            return 'Instant'
        
        if seconds < 60:
            return f"{round(seconds)} seconds"
        
        if seconds < 3600:
            return f"{round(seconds / 60)} minutes"
        
        if seconds < 86400:
            return f"{round(seconds / 3600)} hours"
        
        if seconds < 31536000:
            return f"{round(seconds / 86400)} days"
        
        if seconds < 315360000:  # 10 years
            return f"{round(seconds / 31536000)} years"
        
        if seconds < 31536000000:  # 1000 years
            return "Centuries"
        
        return "Millennia" 