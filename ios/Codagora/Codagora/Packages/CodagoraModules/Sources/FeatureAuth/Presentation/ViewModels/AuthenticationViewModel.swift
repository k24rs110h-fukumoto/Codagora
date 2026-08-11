//
//  AuthenticationViewModel.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

import Combine
import CoreNetworking

public enum AuthenticationRestoreState: Equatable, Sendable {
    case idle
    case loading
    case authenticated(AuthenticatedUser)
    case unauthenticated
    case failed(String)
}

@MainActor
public final class AuthenticationViewModel: ObservableObject {
    @Published public private(set) var state: AuthenticationRestoreState = .idle
    
    private let currentUserUseCase: any CurrentUserUseCaseProtocol
    
    public init(currentUserUseCase: any CurrentUserUseCaseProtocol) {
        self.currentUserUseCase = currentUserUseCase
    }
    
    public func restoreSession() async {
        switch state {
        case .idle, .failed:
            break

        case .loading,
             .authenticated,
             .unauthenticated:
            return
        }

        state = .loading

        do {
            let user = try await currentUserUseCase.execute()
            state = .authenticated(user)
        } catch let error as NetworkError {
            switch error {
            case .unauthorized,
                 .forbidden:
                state = .unauthenticated

            default:
                state = .failed(
                    AuthErrorMapper.message(for: error)
                )
            }
        } catch {
            state = .failed(
                AuthErrorMapper.message(for: error)
            )
        }
    }
}
