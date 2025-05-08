class Validators {
  static String? username(String? v) {
    final val = v?.trim() ?? '';
    if (val.isEmpty) return 'Username is required';
    if (val.length < 3) return 'Username must be at least 3 characters';
    if (val.length > 12) return 'Username must be at most 12 characters';
    // allow only letters, digits, underscore
    if (!RegExp(r'^[A-Za-z0-9_]+$').hasMatch(val)) {
      return 'Only letters, numbers, and underscore allowed';
    }
    return null;
  }

  static String? password(String? v) {
    final val = v ?? '';
    if (val.isEmpty) return 'Password is required';
    if (val.length < 6) return 'Password must be at least 6 characters';
    if (val.length > 12) return 'Password must be at most 12 characters';
    // at least one letter, one digit, one special
    if (!RegExp(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[!@#\$%^&*]).+$').hasMatch(val)) {
      return 'Must include letter, number and special character';
    }
    return null;
  }
}
