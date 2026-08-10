//
//  HTTPMethod.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/02.
//

public enum HTTPMethod: String, Sendable {
    case get = "GET"
    case post = "POST"
    case put = "PUT"
    case patch = "PATCH"
    case delete = "DELETE"
}
