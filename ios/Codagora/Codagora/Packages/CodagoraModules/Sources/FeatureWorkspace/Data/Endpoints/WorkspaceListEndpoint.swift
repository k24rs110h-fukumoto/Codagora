//
//  WorkspaceListEndpoint.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

import CoreNetworking

struct WorkspaceListEndpoint: APIEndpoint {
    typealias Response = [WorkspaceSummary]
    
    let path = "/api/workspaces/"
    let method = HTTPMethod.get
    
    var headers: [String : String] {
        [
            "Accept": "application/json"
        ]
    }
}
