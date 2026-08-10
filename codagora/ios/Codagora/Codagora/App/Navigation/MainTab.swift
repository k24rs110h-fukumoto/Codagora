//
//  MainTab.swift
//  Codagora
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

import Foundation

enum MainTab: CaseIterable, Identifiable, Hashable {
    case home
    case explore
    case workspace
    case activity
    case profile
    
    var id: Self {
        self
    }
    
    var title: String {
        switch self {
        case .home:
            return "home"
        case .explore:
            return "explore"
        case .workspace:
            return "workspace"
        case .activity:
            return "activity"
        case .profile:
            return "profile"
        }
    }
    
    var systemImage: String {
            switch self {
            case .home:
                return "house"

            case .explore:
                return "globe"

            case .workspace:
                return "bubble.left.and.bubble.right"

            case .activity:
                return "sparkles"

            case .profile:
                return "person.crop.circle"
            }
        }
}
