//
//  WorkspaceSection.swift
//  Codagora
//
//  Created by Haruto Fukumoto on 2026/08/08.
//

import Foundation

enum WorkspaceSection:
    CaseIterable,
    Identifiable,
    Hashable
{
    case overview
    case chat
    case tasks
    case github
    case calendar
    case map
    case members
    case files

    var id: Self {
        self
    }

    var title: String {
        switch self {
        case .overview:
            return "Overview"

        case .chat:
            return "Chat"

        case .tasks:
            return "Tasks"

        case .github:
            return "GitHub"

        case .calendar:
            return "Calendar"

        case .map:
            return "Map"

        case .members:
            return "Members"

        case .files:
            return "Files"
        }
    }

    var systemImage: String {
        switch self {
        case .overview:
            return "rectangle.grid.2x2"

        case .chat:
            return "bubble.left.and.bubble.right"

        case .tasks:
            return "checkmark.circle"

        case .github:
            return "chevron.left.forwardslash.chevron.right"

        case .calendar:
            return "calendar"

        case .map:
            return "map"

        case .members:
            return "person.2"

        case .files:
            return "folder"
        }
    }
}
