//
//  APIEndpoint.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/02.
//

import Foundation

public protocol APIEndpoint: Sendable {
    associatedtype Response: Decodable & Sendable
    
    var path: String { get }
    var method: HTTPMethod { get }
    var queryItems: [URLQueryItem] { get }
    var headers: [String: String] { get }
    func makeBody() throws -> Data?
}

public extension APIEndpoint {
    var queryItems: [URLQueryItem] {
        []
    }
    
    var headers: [String: String] {
        [:]
    }
    
    func makeBody() throws -> Data? {
        nil
    }
}
