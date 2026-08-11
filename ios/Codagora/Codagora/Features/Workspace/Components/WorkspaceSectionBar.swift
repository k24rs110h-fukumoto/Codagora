//
//  WorkspaceSectionBar.swift
//  Codagora
//
//  Created by Haruto Fukumoto on 2026/08/08.
//

import SwiftUI

struct WorkspaceSectionBar: View {
    @Binding var selectedSection:
        WorkspaceSection

    var body: some View {
        ScrollView(
            .horizontal,
            showsIndicators: false
        ) {
            HStack(spacing: 8) {
                ForEach(
                    WorkspaceSection.allCases
                ) { section in
                    sectionButton(
                        section
                    )
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
        }
        .background(
            Color("CodagoraCard")
        )
    }

    private func sectionButton(
        _ section: WorkspaceSection
    ) -> some View {
        Button {
            select(
                section
            )
        } label: {
            HStack(spacing: 6) {
                Image(
                    systemName:
                        section.systemImage
                )
                .font(
                    .system(
                        size: 13,
                        weight: .semibold
                    )
                )

                Text(section.title)
                    .font(.subheadline)
                    .fontWeight(
                        selectedSection == section
                            ? .semibold
                            : .regular
                    )
            }
            .foregroundStyle(
                selectedSection == section
                    ? Color("CodagoraBlue")
                    : Color(
                        "CodagoraSecondaryText"
                    )
            )
            .padding(
                .horizontal,
                12
            )
            .padding(
                .vertical,
                8
            )
            .background(
                selectedSection == section
                    ? Color("CodagoraSelection")
                    : Color.clear,
                in: Capsule()
            )
        }
        .buttonStyle(.plain)
    }

    private func select(
        _ section: WorkspaceSection
    ) {
        withAnimation(
            .snappy(duration: 0.22)
        ) {
            selectedSection = section
        }
    }
}
