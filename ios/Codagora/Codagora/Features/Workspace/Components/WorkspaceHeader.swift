//
//  WorkspaceHeader.swift
//  Codagora
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

import SwiftUI
import FeatureWorkspace

struct WorkspaceHeader: View {
    let workspace: WorkspaceSummary
    let workspaces: [WorkspaceSummary]

    let onBack: () -> Void
    let onSelectWorkspace: (WorkspaceSummary) -> Void
    let onCreateInvitation: () -> Void
    let onSettings: () -> Void

    var body: some View {
        HStack(spacing: 10) {
            backButton

            workspaceSelector

            Spacer()

            workspaceMenu
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 10)
        .background(
            Color("CodagoraCard")
        )
    }

    private var backButton: some View {
        Button {
            onBack()
        } label: {
            Image(systemName: "chevron.left")
                .font(
                    .system(
                        size: 17,
                        weight: .semibold
                    )
                )
                .foregroundStyle(
                    Color("CodagoraNavy")
                )
                .frame(
                    width: 38,
                    height: 38
                )
        }
        .buttonStyle(.plain)
    }

    private var workspaceSelector: some View {
        Menu {
            ForEach(workspaces) { item in
                Button {
                    onSelectWorkspace(item)
                } label: {
                    HStack {
                        Text(item.name)

                        if item.id == workspace.id {
                            Image(
                                systemName: "checkmark"
                            )
                        }
                    }
                }
            }
        } label: {
            HStack(spacing: 6) {
                workspaceIcon

                VStack(
                    alignment: .leading,
                    spacing: 2
                ) {
                    Text(workspace.name)
                        .font(.headline)
                        .foregroundStyle(
                            Color("CodagoraNavy")
                        )
                        .lineLimit(1)

                    Text(roleTitle)
                        .font(.caption)
                        .foregroundStyle(
                            Color(
                                "CodagoraSecondaryText"
                            )
                        )
                }

                Image(
                    systemName: "chevron.down"
                )
                .font(
                    .system(
                        size: 11,
                        weight: .semibold
                    )
                )
                .foregroundStyle(
                    Color("CodagoraGray")
                )
            }
        }
        .buttonStyle(.plain)
    }

    private var workspaceIcon: some View {
        Text(
            String(
                workspace.name.prefix(1)
            )
        )
        .font(.caption)
        .fontWeight(.bold)
        .foregroundStyle(
            Color("CodagoraBlue")
        )
        .frame(
            width: 32,
            height: 32
        )
        .background(
            Color("CodagoraSelection"),
            in: RoundedRectangle(
                cornerRadius: 9,
                style: .continuous
            )
        )
    }

    private var workspaceMenu: some View {
        Menu {
            Button {
                onCreateInvitation()
            } label: {
                Label(
                    "メンバーを招待",
                    systemImage:
                        "person.badge.plus"
                )
            }

            Button {
                onSettings()
            } label: {
                Label(
                    "Workspace設定",
                    systemImage: "gearshape"
                )
            }

            Divider()

            Button {
                onBack()
            } label: {
                Label(
                    "Workspace一覧",
                    systemImage:
                        "rectangle.3.group"
                )
            }
        } label: {
            Image(systemName: "ellipsis")
                .font(
                    .system(
                        size: 18,
                        weight: .semibold
                    )
                )
                .foregroundStyle(
                    Color("CodagoraNavy")
                )
                .frame(
                    width: 38,
                    height: 38
                )
        }
        .buttonStyle(.plain)
    }

    private var roleTitle: String {
        guard let role =
                workspace.currentUserRole else {
            return "Workspace"
        }

        switch role {
        case .owner:
            return "Owner"

        case .admin:
            return "Admin"

        case .member:
            return "Member"

        case .guest:
            return "Guest"
        }
    }
}
