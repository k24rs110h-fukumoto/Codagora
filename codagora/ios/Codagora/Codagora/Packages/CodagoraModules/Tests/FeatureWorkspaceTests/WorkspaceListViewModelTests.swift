//
//  WorkspaceListViewModel.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

import Foundation
import Testing
@testable import FeatureWorkspace

@Suite("WorkspaceListViewModel")
@MainActor
struct WorkspaceListViewModelTests {
    @Test("ワークスペース一覧を取得する")
    func loadsWorkspaces() async {
        let workspace = makeWorkspace()

        let useCase = MockFetchWorkspacesUseCase(
            result: .success([
                workspace
            ])
        )

        let viewModel = WorkspaceListViewModel(
            fetchWorkspacesUseCase: useCase
        )

        await viewModel.load()

        #expect(viewModel.workspaces.count == 1)
        #expect(
            viewModel.workspaces.first?.id
                == workspace.id
        )
        #expect(viewModel.errorMessage == nil)
        #expect(viewModel.isLoading == false)
    }

    @Test("0件の場合はisEmptyがtrueになる")
    func becomesEmptyWhenNoWorkspaces() async {
        let useCase = MockFetchWorkspacesUseCase(
            result: .success([])
        )

        let viewModel = WorkspaceListViewModel(
            fetchWorkspacesUseCase: useCase
        )

        await viewModel.load()

        #expect(viewModel.workspaces.isEmpty)
        #expect(viewModel.isEmpty)
        #expect(viewModel.errorMessage == nil)
    }

    @Test("取得失敗時にエラーメッセージを設定する")
    func showsErrorWhenLoadingFails() async {
        let useCase = MockFetchWorkspacesUseCase(
            result: .failure(.requestFailed)
        )

        let viewModel = WorkspaceListViewModel(
            fetchWorkspacesUseCase: useCase
        )

        await viewModel.load()

        #expect(viewModel.workspaces.isEmpty)
        #expect(
            viewModel.errorMessage
                == "ワークスペース一覧の取得に失敗しました"
        )
        #expect(viewModel.isLoading == false)
    }

    private func makeWorkspace()
        -> WorkspaceSummary {
        WorkspaceSummary(
            id: "workspace-1",
            name: "Codagora Development",
            slug: "codagora-development",
            description: "開発用ワークスペース",
            owner: WorkspaceOwner(
                id: "user-1",
                displayName: "管理者",
                avatarUrl: ""
            ),
            currentUserRole: .owner,
            activeMemberCount: 1,
            createdAt: Date(
                timeIntervalSince1970: 0
            ),
            updatedAt: Date(
                timeIntervalSince1970: 0
            )
        )
    }
}

private struct MockFetchWorkspacesUseCase:
    FetchWorkspacesUseCaseProtocol,
    Sendable
{
    let result: Result<
        [WorkspaceSummary],
        MockWorkspaceError
    >

    func execute() async throws
        -> [WorkspaceSummary] {
        switch result {
        case let .success(workspaces):
            return workspaces

        case let .failure(error):
            throw error
        }
    }
}

private enum MockWorkspaceError:
    Error,
    Sendable
{
    case requestFailed
}
