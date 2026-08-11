//
//  WorkspaceView.swift
//  Codagora
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

import SwiftUI
import FeatureWorkspace

@MainActor
struct WorkspaceView: View {
    @StateObject private var workspaceListViewModel:
        WorkspaceListViewModel

    @State private var selectedWorkspace:
        WorkspaceSummary?

    @State private var selectedSection:
        WorkspaceSection = .overview

    init(
        workspaceListViewModel:
            WorkspaceListViewModel
    ) {
        _workspaceListViewModel = StateObject(
            wrappedValue:
                workspaceListViewModel
        )
    }

    var body: some View {
        NavigationStack {
            Group {
                if let selectedWorkspace {
                    selectedWorkspaceContent(
                        workspace:
                            selectedWorkspace
                    )
                } else {
                    workspaceSelectionContent
                }
            }
            .frame(
                maxWidth: .infinity,
                maxHeight: .infinity
            )
            .background(
                Color("CodagoraBackground")
                    .ignoresSafeArea()
            )
            .toolbar(
                .hidden,
                for: .navigationBar
            )
        }
    }

    private var workspaceSelectionContent:
        some View {
        VStack(spacing: 0) {
            workspaceListHeader

            Divider()
                .overlay(
                    Color("CodagoraBorder")
                )

            WorkspaceListView(
                viewModel:
                    workspaceListViewModel,
                onSelectWorkspace: {
                    workspace in

                    selectWorkspace(
                        workspace
                    )
                }
            )
        }
    }

    private var workspaceListHeader:
        some View {
        HStack(spacing: 12) {
            Text("Workspace")
                .font(.title2)
                .fontWeight(.bold)
                .foregroundStyle(
                    Color("CodagoraNavy")
                )

            Spacer()

            Button {
            } label: {
                Image(
                    systemName: "plus"
                )
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
        .padding(.horizontal, 20)
        .padding(.vertical, 10)
        .background(
            Color("CodagoraCard")
        )
    }

    private func selectedWorkspaceContent(
        workspace: WorkspaceSummary
    ) -> some View {
        VStack(spacing: 0) {
            WorkspaceHeader(
                workspace: workspace,
                workspaces:
                    workspaceListViewModel.workspaces,
                onBack: {
                    leaveWorkspace()
                },
                onSelectWorkspace: { workspace in
                    selectWorkspace(workspace)
                },
                onCreateInvitation: {
                },
                onSettings: {
                }
            )

            Divider()
                .overlay(
                    Color("CodagoraBorder")
                )

            WorkspaceSectionBar(
                selectedSection:
                    $selectedSection
            )

            Divider()
                .overlay(
                    Color("CodagoraBorder")
                )

            sectionContent(
                workspace: workspace
            )
        }
    }

    private func selectedWorkspaceHeader(
        workspace: WorkspaceSummary
    ) -> some View {
        HStack(spacing: 12) {
            Button {
                leaveWorkspace()
            } label: {
                Image(
                    systemName: "chevron.left"
                )
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

                Text(
                    selectedSection.title
                )
                .font(.caption)
                .foregroundStyle(
                    Color(
                        "CodagoraSecondaryText"
                    )
                )
            }

            Spacer()

            Button {
            } label: {
                Image(
                    systemName: "ellipsis"
                )
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
        .padding(.horizontal, 12)
        .padding(.vertical, 10)
        .background(
            Color("CodagoraCard")
        )
    }

    @ViewBuilder
    private func sectionContent(
        workspace: WorkspaceSummary
    ) -> some View {
        switch selectedSection {
        case .overview:
            placeholderSection(
                title: "Overview",
                systemImage:
                    "rectangle.grid.2x2",
                description:
                    "\(workspace.name)の概要"
            )

        case .chat:
            placeholderSection(
                title: "Chat",
                systemImage:
                    "bubble.left.and.bubble.right",
                description:
                    "チャンネルやメッセージを表示します"
            )

        case .tasks:
            placeholderSection(
                title: "Tasks",
                systemImage:
                    "checkmark.circle",
                description:
                    "ワークスペースのタスクを管理します"
            )

        case .github:
            placeholderSection(
                title: "GitHub",
                systemImage:
                    "chevron.left.forwardslash.chevron.right",
                description:
                    "GitHub連携情報を表示します"
            )

        case .calendar:
            placeholderSection(
                title: "Calendar",
                systemImage: "calendar",
                description:
                    "予定やイベントを表示します"
            )

        case .map:
            placeholderSection(
                title: "Map",
                systemImage: "map",
                description:
                    "メンバーの作業場所を共有します"
            )

        case .members:
            placeholderSection(
                title: "Members",
                systemImage: "person.2",
                description:
                    "参加メンバーを表示します"
            )

        case .files:
            placeholderSection(
                title: "Files",
                systemImage: "folder",
                description:
                    "共有ファイルを表示します"
            )
        }
    }

    private func placeholderSection(
        title: String,
        systemImage: String,
        description: String
    ) -> some View {
        VStack(spacing: 14) {
            Image(
                systemName: systemImage
            )
            .font(.system(size: 36))
            .foregroundStyle(
                Color("CodagoraBlue")
            )

            Text(title)
                .font(.title3)
                .fontWeight(.bold)
                .foregroundStyle(
                    Color("CodagoraNavy")
                )

            Text(description)
                .font(.subheadline)
                .foregroundStyle(
                    Color(
                        "CodagoraSecondaryText"
                    )
                )
                .multilineTextAlignment(
                    .center
                )
        }
        .frame(
            maxWidth: .infinity,
            maxHeight: .infinity
        )
        .padding(24)
    }

    private func selectWorkspace(
        _ workspace: WorkspaceSummary
    ) {
        withAnimation(
            .snappy(duration: 0.25)
        ) {
            selectedWorkspace = workspace
            selectedSection = .overview
        }
    }

    private func leaveWorkspace() {
        withAnimation(
            .snappy(duration: 0.25)
        ) {
            selectedWorkspace = nil
            selectedSection = .overview
        }
    }
}
