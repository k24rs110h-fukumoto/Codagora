//
//  ValidationUtility.swift
//  Codagora
//
//  Created by Haruto Fukumoto on 2026/08/01.
//

import Foundation

public enum ValidationUtility {
    private static let userNamePattern = "^[A-Za-z0-9-]{1,30}$"
    
    private static let emailPattern = "^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$"
    
    public static func isValidName(_ name: String) -> Bool {
        let trimmedName = name.trimmingCharacters(in: .whitespacesAndNewlines)
        
        return !trimmedName.isEmpty
    }
    
    public static func isValidUsername(_ userName: String) -> Bool {
        userName.range(of: userNamePattern, options: .regularExpression) != nil
    }
    
    public static func isValidEmail(_ email: String) -> Bool {
        let trimmedEmail = email.trimmingCharacters(in: .whitespacesAndNewlines)
        
        return trimmedEmail.range(of: emailPattern, options: .regularExpression) != nil
    }
    
    public static func hasValidPasswordLength(_ password: String) -> Bool {
        password.count >= 8
    }
    
    public static func containsUppercase(_ password: String) -> Bool {
        password.range(of: "[A-Z]", options: .regularExpression) != nil
    }
    
    public static func containsLowercase(_ password: String) -> Bool {
        password.range(of: "[a-z]", options: .regularExpression) != nil
    }
    
    public static func containsNumber(_ password: String) -> Bool {
        password.range(of: "[0-9]", options: .regularExpression) != nil
    }
    
    public static func isValidPassword(_ password: String) -> Bool {
        hasValidPasswordLength(password) &&
        containsUppercase(password) &&
        containsLowercase(password) &&
        containsNumber(password)
    }
    
    public static func passwordsMatch(_ password: String, _ confirmPassword: String) -> Bool {
        !confirmPassword.isEmpty && password == confirmPassword
    }
}
