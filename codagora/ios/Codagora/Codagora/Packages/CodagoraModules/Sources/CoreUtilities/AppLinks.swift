//
//  AppLinks.swift
//  Codagora
//
//  Created by Haruto Fukumoto on 2026/07/31.
//

import Foundation

public enum AppLinks {
    public static let terms = makeURL("https://example.com/terms")
    
    public static let privacyPolicy = makeURL("https://example.com/privacy")
    
    public static let contact = makeURL("https://example.com/contact")
    
    private static func makeURL(_ value: String) -> URL {
        guard let url = URL(string: value) else {
            fatalError("不正なURLです: \(value)")
        }
        return url
    }
}
