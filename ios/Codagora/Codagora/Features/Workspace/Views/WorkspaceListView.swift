//
//  WorkspaceListView.swift
//  Codagora
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

import SwiftUI
import FeatureWorkspace

@MainActor
struct WorkspaceListView: View {
    @StateObject private var viewModel:
        WorkspaceListViewModel

    let onSelectWorkspace:
        (WorkspaceSummary) -> Void

    init(
        viewModel: WorkspaceListViewModel,
        onSelectWorkspace:
            @escaping (WorkspaceSummary) -> Void
    ) {
        _viewModel = StateObject(
            wrappedValue: viewModel
        )

        self.onSelectWorkspace =
            onSelectWorkspace
    }

    var body: some View {
        content
            .background(
                Color("CodagoraBackground")
            )
            .task {
                await viewModel.load()
            }
    }

    @ViewBuilder
    private var content: some View {
        if viewModel.isLoading &&
            viewModel.workspaces.isEmpty {
            loadingView

        } else if let errorMessage =
                    viewModel.errorMessage,
                  viewModel.workspaces.isEmpty {
            errorView(
                message: errorMessage
            )

        } else if viewModel.isEmpty {
            emptyView

        } else {
            workspaceList
        }
    }

    private var loadingView: some View {
        VStack(spacing: 14) {
            ProgressView()

            Text(
                "ワークスペースを読み込んでいます"
            )
            .font(.subheadline)
            .foregroundStyle(
                Color("CodagoraSecondaryText")
            )
        }
        .frame(
            maxWidth: .infinity,
            maxHeight: .infinity
        )
    }

    private var workspaceList: some View {
        List {
            ForEach(
                viewModel.workspaces
            ) { workspace in
                Button {
                    onSelectWorkspace(
                        workspace
                    )
                } label: {
                    workspaceRow(
                        workspace: workspace
                    )
                }
                .buttonStyle(.plain)
                .listRowBackground(
                    Color("CodagoraCard")
                )
            }
        }
        .listStyle(.plain)
        .scrollContentBackground(.hidden)
        .background(
            Color("CodagoraBackground")
        )
        .refreshable {
            await viewModel.reload()
        }
    }

    private func workspaceRow(
        workspace: WorkspaceSummary
    ) -> some View {
        VStack(
            alignment: .leading,
            spacing: 10
        ) {
            HStack(
                alignment: .center,
                spacing: 12
            ) {
                workspaceIcon(
                    workspace: workspace
                )

                VStack(
                    alignment: .leading,
                    spacing: 4
                ) {
                    Text(workspace.name)
                        .font(.headline)
                        .foregroundStyle(
                            Color(
                                "CodagoraNavy"
                            )
                        )

                    if !workspace
                        .description
                        .isEmpty {
                        Text(
                            workspace.description
                        )
                        .font(.subheadline)
                        .foregroundStyle(
                            Color(
                                "CodagoraSecondaryText"
                            )
                        )
                        .lineLimit(2)
                    }
                }

                Spacer()

                Image(
                    systemName:
                        "chevron.right"
                )
                .font(
                    .system(
                        size: 13,
                        weight: .semibold
                    )
                )
                .foregroundStyle(
                    Color("CodagoraGray")
                )
            }

            HStack(spacing: 14) {
                Label(
                    "\(workspace.activeMemberCount)人",
                    systemImage: "person.2"
                )

                if let role =
                    workspace.currentUserRole {
                    Label(
                        roleTitle(role),
                        systemImage:
                            "person.badge.shield.checkmark"
                    )
                }
            }
            .font(.caption)
            .foregroundStyle(
                Color(
                    "CodagoraSecondaryText"
                )
            )
        }
        .padding(.vertical, 10)
    }

    private func workspaceIcon(
        workspace: WorkspaceSummary
    ) -> some View {
        Text(
            String(
                workspace.name.prefix(1)
            )
        )
        .font(.headline)
        .fontWeight(.bold)
        .foregroundStyle(
            Color("CodagoraBlue")
        )
        .frame(
            width: 44,
            height: 44
        )
        .background(
            Color("CodagoraSelection"),
            in: RoundedRectangle(
                cornerRadius: 12,
                style: .continuous
            )
        )
    }

    private var emptyView: some View {
        ContentUnavailableView {
            Label(
                "ワークスペースがありません",
                systemImage:
                    "rectangle.3.group"
            )
            .foregroundStyle(
                Color("CodagoraNavy")
            )
        } description: {
            Text(
                "ワークスペースを作成するか、招待から参加してください。"
            )
            .foregroundStyle(
                Color(
                    "CodagoraSecondaryText"
                )
            )
        }
        .frame(
            maxWidth: .infinity,
            maxHeight: .infinity
        )
    }

    private func errorView(
        message: String
    ) -> some View {
        ContentUnavailableView {
            Label(
                "読み込みに失敗しました",
                systemImage:
                    "exclamationmark.triangle"
            )
            .foregroundStyle(
                Color("CodagoraError")
            )
        } description: {
            Text(message)
                .foregroundStyle(
                    Color(
                        "CodagoraSecondaryText"
                    )
                )
        } actions: {
            Button("再試行") {
                Task {
                    await viewModel.reload()
                }
            }
            .foregroundStyle(
                Color("CodagoraBlue")
            )
        }
        .frame(
            maxWidth: .infinity,
            maxHeight: .infinity
        )
    }

    private func roleTitle(
        _ role: WorkspaceRole
    ) -> String {
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
