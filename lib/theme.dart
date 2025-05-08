// lib/theme.dart

import 'package:flutter/material.dart';

/// AppTheme defines the application's color palette and theme data
/// to match the app logo's blue and white styling.
class AppTheme {
  AppTheme._(); // Private constructor to prevent instantiation

  // Primary blue extracted from the logo (approx. #0261D6)
  static const Color primaryColor = Color(0xFF0261D6);
  static const Color primaryLightColor = Color(0xFF4A8AF2);
  static const Color primaryDarkColor = Color(0xFF01549A);

  // Accent and on-colors
  static const Color accentColor = primaryColor;
  static const Color onPrimary = Colors.white;
  static const Color backgroundColor = Colors.white;

  // Generate a swatch from our primary color
  static final MaterialColor primarySwatch = _createMaterialColor(primaryColor);

  /// The main ThemeData for the app
  static final ThemeData theme = ThemeData(
    primarySwatch: primarySwatch,
    primaryColor: primaryColor,
    brightness: Brightness.light,
    scaffoldBackgroundColor: backgroundColor,
    colorScheme: ColorScheme.light(
      primary: primaryColor,
      primaryContainer: primaryDarkColor,
      secondary: accentColor,
      onPrimary: onPrimary,
      background: backgroundColor,
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: primaryColor,
      foregroundColor: onPrimary,
      elevation: 0,
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: primaryColor,
        foregroundColor: onPrimary,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: primaryColor,
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: const BorderSide(color: primaryColor),
      ),
    ),
  );

  /// Creates a MaterialColor from a single [color].
  static MaterialColor _createMaterialColor(Color color) {
    final strengths = <double>[.05];
    final swatch = <int, Color>{};
    final r = color.red, g = color.green, b = color.blue;

    for (int i = 1; i < 10; i++) {
      strengths.add(0.1 * i);
    }
    for (double strength in strengths) {
      final double ds = 0.5 - strength;
      swatch[(strength * 1000).round()] = Color.fromRGBO(
        r + ((ds < 0 ? r : (255 - r)) * ds).round(),
        g + ((ds < 0 ? g : (255 - g)) * ds).round(),
        b + ((ds < 0 ? b : (255 - b)) * ds).round(),
        1,
      );
    }
    return MaterialColor(color.value, swatch);
  }
}
