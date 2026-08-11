//
//  CurrentUserEndpoint.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

import Foundation
import CoreNetworking

struct CurrentUserEndpoint: APIEndpoint {
    typealias Response = CurrentUserResponse
    
    let path = "/api/auth/me/"
    let method = HTTPMethod.get
    
    var headers: [String : String] {
        ["Accept": "application/json"]
    }
}
