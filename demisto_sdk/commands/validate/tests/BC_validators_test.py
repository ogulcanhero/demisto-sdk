from typing import List

import pytest

from demisto_sdk.commands.common.constants import GitStatuses, MarketplaceVersions
from demisto_sdk.commands.content_graph.objects import Integration
from demisto_sdk.commands.content_graph.objects.integration import Command, Output
from demisto_sdk.commands.content_graph.objects.script import Script
from demisto_sdk.commands.validate.tests.test_tools import (
    REPO,
    create_incident_type_object,
    create_incoming_mapper_object,
    create_integration_object,
    create_old_file_pointers,
    create_pack_object,
    create_script_object,
)
from demisto_sdk.commands.validate.validators.BC_validators.BC100_breaking_backwards_subtype import (
    BreakingBackwardsSubtypeValidator,
)
from demisto_sdk.commands.validate.validators.BC_validators.BC101_is_breaking_context_output_backwards import (
    IsBreakingContextOutputBackwardsValidator,
)
from demisto_sdk.commands.validate.validators.BC_validators.BC102_is_context_path_changed import (
    IsContextPathChangedValidator,
)
from demisto_sdk.commands.validate.validators.BC_validators.BC103_args_name_change import (
    ArgsNameChangeValidator,
)
from demisto_sdk.commands.validate.validators.BC_validators.BC105_id_changed import (
    IdChangedValidator,
)
from demisto_sdk.commands.validate.validators.BC_validators.BC106_is_valid_fromversion_on_modified import (
    IsValidFromversionOnModifiedValidator,
)
from demisto_sdk.commands.validate.validators.BC_validators.BC107_is_valid_toversion_on_modified import (
    IsValidToversionOnModifiedValidator,
)
from demisto_sdk.commands.validate.validators.BC_validators.BC108_was_marketplace_modified import (
    WasMarketplaceModifiedValidator,
)
from TestSuite.repo import ChangeCWD

ALL_MARKETPLACES = list(MarketplaceVersions)
XSIAM_MARKETPLACE = [ALL_MARKETPLACES[1]]
ALL_MARKETPLACES_FOR_IN_PACK = [marketplace.value for marketplace in ALL_MARKETPLACES]
XSIAM_MARKETPLACE_FOR_IN_PACK = [ALL_MARKETPLACES_FOR_IN_PACK[1]]
XSOAR_MARKETPLACE = [ALL_MARKETPLACES[0]]
XSOAR_MARKETPLACE_FOR_IN_PACK = [ALL_MARKETPLACES_FOR_IN_PACK[0]]


@pytest.mark.parametrize(
    "content_items, old_content_items, expected_number_of_failures, expected_msgs",
    [
        (
            [
                create_integration_object(paths=["script.subtype"], values=["python2"]),
                create_integration_object(),
            ],
            [create_integration_object(), create_integration_object()],
            1,
            [
                "Possible backwards compatibility break, You've changed the Integration subtype from python3 to python2, please undo."
            ],
        ),
        (
            [
                create_integration_object(paths=["script.subtype"], values=["python2"]),
                create_script_object(),
            ],
            [create_integration_object(), create_script_object()],
            1,
            [
                "Possible backwards compatibility break, You've changed the Integration subtype from python3 to python2, please undo."
            ],
        ),
        (
            [
                create_integration_object(paths=["script.subtype"], values=["python2"]),
                create_script_object(paths=["subtype"], values=["python2"]),
            ],
            [create_integration_object(), create_script_object()],
            2,
            [
                "Possible backwards compatibility break, You've changed the Integration subtype from python3 to python2, please undo.",
                "Possible backwards compatibility break, You've changed the Script subtype from python3 to python2, please undo.",
            ],
        ),
        (
            [create_integration_object(), create_script_object()],
            [create_integration_object(), create_script_object()],
            0,
            [],
        ),
    ],
)
def test_BreakingBackwardsSubtypeValidator_is_valid(
    content_items, old_content_items, expected_number_of_failures, expected_msgs
):
    """
    Given
    content_items and old_content_items iterables.
        - Case 1: content_items with 2 integrations where the first one has its subtype altered, and two integration with no changes in old_content_items.
        - Case 2: content_items with 1 integration where the first one has its subtype altered and one script with no subtype altered, and old_content_items with one script and integration with no changes.
        - Case 3: content_items with 1 integration where the first one has its subtype altered and 1 script where that has its subtype altered, and old_content_items with one script and integration with no changes.
        - Case 4: content_items and old_content_items with 1 integration and 1 script both with no changes
    When
    - Calling the BreakingBackwardsSubtypeValidator is valid function.
    Then
        - Make sure the right amount of failures return and that the right message is returned.
        - Case 1: Should fail 1 integration.
        - Case 2: Should fail 1 integration.
        - Case 3: Should fail both the integration and the script
        - Case 4: Shouldn't fail any content item.
    """
    create_old_file_pointers(content_items, old_content_items)
    results = BreakingBackwardsSubtypeValidator().is_valid(content_items)
    assert len(results) == expected_number_of_failures
    assert all(
        [
            result.message == expected_msg
            for result, expected_msg in zip(results, expected_msgs)
        ]
    )


@pytest.mark.parametrize(
    "content_item, expected_subtype, expected_fix_msg",
    [
        (
            create_integration_object(paths=["script.subtype"], values=["python2"]),
            "python3",
            "Changing subtype back to (python3).",
        ),
        (
            create_script_object(paths=["subtype"], values=["python2"]),
            "python3",
            "Changing subtype back to (python3).",
        ),
    ],
)
def test_BreakingBackwardsSubtypeValidator_fix(
    content_item, expected_subtype, expected_fix_msg
):
    """
    Given
        - content_item.
        - Case 1: an Integration content item where the subtype is different from the subtype of the old_content_item.
        - Case 2: a Script content item where the subtype is different from the subtype of the old_content_item.
    When
    - Calling the BreakingBackwardsSubtypeValidator fix function.
    Then
        - Make sure the the object subtype was changed to match the old_content_item subtype, and that the right fix msg is returned.
    """
    validator = BreakingBackwardsSubtypeValidator()
    validator.old_subtype[content_item.name] = "python3"
    assert validator.fix(content_item).message == expected_fix_msg
    assert content_item.subtype == expected_subtype


@pytest.mark.parametrize(
    "content_items, old_content_items, expected_number_of_failures, old_id, expected_msgs",
    [
        (
            [
                create_integration_object(paths=["commonfields.id"], values=["id_2"]),
                create_integration_object(),
            ],
            [
                create_integration_object(paths=["commonfields.id"], values=["id_1"]),
                create_integration_object(),
            ],
            1,
            {"TestIntegration": "id_1"},
            [
                "ID of content item was changed from id_1 to id_2, please undo.",
            ],
        ),
        (
            [
                create_script_object(paths=["commonfields.id"], values=["id_2"]),
                create_integration_object(),
            ],
            [
                create_script_object(paths=["commonfields.id"], values=["id_1"]),
                create_integration_object(),
            ],
            1,
            {"myScript": "id_1"},
            [
                "ID of content item was changed from id_1 to id_2, please undo.",
            ],
        ),
        (
            [
                create_integration_object(paths=["commonfields.id"], values=["id_2"]),
                create_script_object(paths=["commonfields.id"], values=["id_4"]),
            ],
            [
                create_integration_object(paths=["commonfields.id"], values=["id_1"]),
                create_script_object(paths=["commonfields.id"], values=["id_3"]),
            ],
            2,
            {"TestIntegration": "id_1", "myScript": "id_3"},
            [
                "ID of content item was changed from id_1 to id_2, please undo.",
                "ID of content item was changed from id_3 to id_4, please undo.",
            ],
        ),
        (
            [
                create_integration_object(),
                create_script_object(),
            ],
            [
                create_integration_object(),
                create_script_object(),
            ],
            0,
            {},
            [],
        ),
    ],
)
def test_IdChangedValidator(
    content_items, old_content_items, expected_number_of_failures, old_id, expected_msgs
):
    """
    Given
    content_items and old_content_items iterables.
        - Case 1: content_items with 2 integrations where the first one has its id changed.
        - Case 2: content_items with 1 integration that has its id changed, and one script with no id changed.
        - Case 3: content_items with 1 integration that has its id changed, and one script that has its id changed.
        - Case 4: content_items with 1 integration and 1 script, both with no changes.
    When
    - Calling the IdChangedValidator is valid function.
    Then
        - Make sure the right amount of failures and messages are returned, and that we construct the "old_id" object correctly.
        - Case 1: Should fail 1 integration.
        - Case 2: Should fail 1 script.
        - Case 3: Should fail both the integration and the script
        - Case 4: Shouldn't fail any content item.
    """
    create_old_file_pointers(content_items, old_content_items)
    validator = IdChangedValidator()
    results = validator.is_valid(content_items)
    assert validator.old_id == old_id
    assert len(results) == expected_number_of_failures
    assert all(
        [
            result.message == expected_msg
            for result, expected_msg in zip(results, expected_msgs)
        ]
    )


@pytest.mark.parametrize(
    "content_item, expected_id, expected_fix_msg",
    [
        (
            create_integration_object(paths=["commonfields.id"], values=["id_2"]),
            "id_1",
            "Changing ID back to id_1.",
        ),
        (
            create_script_object(paths=["commonfields.id"], values=["id_2"]),
            "id_1",
            "Changing ID back to id_1.",
        ),
    ],
)
def test_IdChangedValidator_fix(content_item, expected_id, expected_fix_msg):
    """
    Given
        - content_item.
        - Case 1: an Integration content item where its id has changed.
        - Case 2: a Script content item where its id has changed.
    When
    - Calling the IdChangedValidator fix function.
    Then
        - Make sure the the id was changed to match the old_content_item id, and that the right fix message is returned.
    """
    validator = IdChangedValidator()
    validator.old_id[content_item.name] = expected_id
    assert validator.fix(content_item).message == expected_fix_msg
    assert content_item.object_id == expected_id


@pytest.mark.parametrize(
    "old_marketplaces, in_pack_marketplaces",
    [
        (ALL_MARKETPLACES, XSIAM_MARKETPLACE_FOR_IN_PACK),
        (XSIAM_MARKETPLACE, ALL_MARKETPLACES_FOR_IN_PACK),
        (XSIAM_MARKETPLACE, XSIAM_MARKETPLACE_FOR_IN_PACK),
    ],
)
def test_WasMarketplaceModifiedValidator__modified_item_has_only_one_marketplace__passes(
    old_marketplaces, in_pack_marketplaces
):
    """
    Given:
        - Modified `Integration` and `Script` and Old `Integration` and `Script` iterables, each within a pack.
        - Modified `Integration` and `Script` have only `XSIAM` in their level.
        - Case 1: Old `Integration` and `Script` have all marketplaces in their level, and the pack has only `XSIAM`.
        - Case 2: Old `Integration` and `Script` have only `XSIAM`, and the pack has all marketplaces.
        - Case 3: Old `Integration` and `Script` have only `XSIAM`, and the pack has only one marketplace (`XSIAM`).

    When:
        - Calling the `WasMarketplaceModifiedValidator` function.

    Then:
        - The results should be as expected.
        - Case 1: Should pass the validation since although the user defined only `XSIAM`, the content item will be used only in the `XSIAM` marketplace as defined in the pack level.
        - Case 2: Should pass the validation since the user did not remove any marketplace.
        - Case 3: Should pass the validation since the user did not remove any marketplace.
    """
    modified_content_items = [
        create_integration_object(pack_info={"marketplaces": in_pack_marketplaces}),
        create_script_object(pack_info={"marketplaces": in_pack_marketplaces}),
    ]
    old_content_items = [create_integration_object(), create_script_object()]

    modified_content_items[0].marketplaces = modified_content_items[
        1
    ].marketplaces = XSIAM_MARKETPLACE
    old_content_items[0].marketplaces = old_content_items[
        1
    ].marketplaces = old_marketplaces
    create_old_file_pointers(modified_content_items, old_content_items)

    with ChangeCWD(REPO.path):
        assert WasMarketplaceModifiedValidator().is_valid(modified_content_items) == []


@pytest.mark.parametrize(
    "old_marketplaces, in_pack_marketplaces",
    [
        (ALL_MARKETPLACES, ALL_MARKETPLACES_FOR_IN_PACK),
        (XSOAR_MARKETPLACE, ALL_MARKETPLACES_FOR_IN_PACK),
    ],
)
def test_WasMarketplaceModifiedValidator__modified_item_has_only_one_marketplace__fails(
    old_marketplaces, in_pack_marketplaces
):
    """
    Given:
        - Modified `Integration` and `Script` and Old `Integration` and `Script` iterables, each within a pack.
        - Modified `Integration` and `Script` have only `XSIAM` in their level.
        - Case 1: Old `Integration` and `Script` have all marketplaces in their level, and the pack has all marketplaces.
        - Case 2: Old `Integration` and `Script` have only `XSOAR`, and the pack has all marketplaces.

    When:
        - Calling the `WasMarketplaceModifiedValidator` function.

    Then:
        - The results should be as expected.
        - Case 1: Should fail the validation since the user removed marketplaces.
        - Case 2: Should fail the validation since the user replaced one marketplace with a different one.
    """
    modified_content_items = [
        create_integration_object(pack_info={"marketplaces": in_pack_marketplaces}),
        create_script_object(pack_info={"marketplaces": in_pack_marketplaces}),
    ]
    old_content_items = [create_integration_object(), create_script_object()]

    modified_content_items[0].marketplaces = modified_content_items[
        1
    ].marketplaces = XSIAM_MARKETPLACE
    old_content_items[0].marketplaces = old_content_items[
        1
    ].marketplaces = old_marketplaces
    create_old_file_pointers(modified_content_items, old_content_items)

    with ChangeCWD(REPO.path):
        results = WasMarketplaceModifiedValidator().is_valid(modified_content_items)
        assert (
            results[0].message
            == "You can't delete current marketplaces or add new ones if doing so will remove existing ones. Please undo the change or request a forced merge."
        )
        assert len(results) == 2


@pytest.mark.parametrize(
    "modified_marketplaces, in_pack_marketplaces",
    [
        (ALL_MARKETPLACES, XSIAM_MARKETPLACE_FOR_IN_PACK),
        (ALL_MARKETPLACES, ALL_MARKETPLACES_FOR_IN_PACK),
    ],
)
def test_WasMarketplaceModifiedValidator__old_item_has_only_one_marketplace__passes(
    modified_marketplaces, in_pack_marketplaces
):
    """
    Given:
        - Modified `Integration` and `Script` and Old `Integration` and `Script` iterables, each within a pack.
        - Old `Integration` and `Script` have only `XSIAM` in their level.
        - Case 1: Modified `Integration` and `Script` have all marketplaces in their level, and the pack has only `XSIAM`.
        - Case 2: Modified `Integration` and `Script` have all marketplaces in their level, and the pack has all marketplaces.

    When:
        - Calling the `WasMarketplaceModifiedValidator` function.

    Then:
        - The results should be as expected.
        - Case 1: Should pass the validation since the user added marketplaces or removed all marketplaces which is equal to adding all marketplaces.
        - Case 2: Should pass the validation since the user added marketplaces or removed all marketplaces which is equal to adding all marketplaces.
    """
    modified_content_items = [
        create_integration_object(pack_info={"marketplaces": in_pack_marketplaces}),
        create_script_object(pack_info={"marketplaces": in_pack_marketplaces}),
    ]
    old_content_items = [create_integration_object(), create_script_object()]

    modified_content_items[0].marketplaces = modified_content_items[
        1
    ].marketplaces = modified_marketplaces
    old_content_items[0].marketplaces = old_content_items[
        1
    ].marketplaces = XSIAM_MARKETPLACE
    create_old_file_pointers(modified_content_items, old_content_items)

    with ChangeCWD(REPO.path):
        assert WasMarketplaceModifiedValidator().is_valid(modified_content_items) == []


def test_WasMarketplaceModifiedValidator__old_item_has_only_one_marketplace__fails():
    """
    Given:
        - Modified `Integration` and `Script` and Old `Integration` and `Script` iterables, each within a pack.
        - Old `Integration` and `Script` have only `XSIAM` in their level.
        - Modified `Integration` and `Script` have only `XSOAR`, and the pack has all marketplaces.

    When:
        - Calling the `WasMarketplaceModifiedValidator` function.

    Then:
        - The results should be as expected.
        - Should fail the validation since the user replaced one marketplace with a different one.

    """
    modified_marketplaces = XSOAR_MARKETPLACE
    in_pack_marketplaces = ALL_MARKETPLACES_FOR_IN_PACK

    modified_content_items = [
        create_integration_object(pack_info={"marketplaces": in_pack_marketplaces}),
        create_script_object(pack_info={"marketplaces": in_pack_marketplaces}),
    ]
    old_content_items = [create_integration_object(), create_script_object()]

    modified_content_items[0].marketplaces = modified_content_items[
        1
    ].marketplaces = modified_marketplaces
    old_content_items[0].marketplaces = old_content_items[
        1
    ].marketplaces = XSIAM_MARKETPLACE
    create_old_file_pointers(modified_content_items, old_content_items)

    with ChangeCWD(REPO.path):
        results = WasMarketplaceModifiedValidator().is_valid(modified_content_items)
        assert (
            results[0].message
            == "You can't delete current marketplaces or add new ones if doing so will remove existing ones. Please undo the change or request a forced merge."
        )
        assert len(results) == 2


@pytest.mark.parametrize(
    "in_pack_marketplaces",
    [
        (XSIAM_MARKETPLACE_FOR_IN_PACK),
        (ALL_MARKETPLACES_FOR_IN_PACK),
    ],
)
def test_WasMarketplaceModifiedValidator__old_and_modified_items_have_all_marketplace(
    in_pack_marketplaces,
):
    """
    Given:
        - Modified `Integration` and `Script` and Old `Integration` and `Script` iterables, each within a pack.
        - Modified `Integration` and `Script` have all marketplaces in their level.
        - Old `Integration` and `Script` have all marketplaces in their level.
        - Case 1: Pack has only `XSIAM`.
        - Case 2: Pack has all marketplaces.

    When:
        - Calling the `WasMarketplaceModifiedValidator` function.

    Then:
        - The results should be as expected.
        - Case 1: Should pass the validation since the user added marketplaces or removed all marketplaces which is equal to adding all marketplaces.
        - Case 2: Should pass the validation since the user didn't change anything or removed all marketplaces which is equal to adding all marketplaces.
    """

    modified_content_items = [
        create_integration_object(pack_info={"marketplaces": in_pack_marketplaces}),
        create_script_object(pack_info={"marketplaces": in_pack_marketplaces}),
    ]
    old_content_items = [create_integration_object(), create_script_object()]

    create_old_file_pointers(modified_content_items, old_content_items)
    with ChangeCWD(REPO.path):
        assert WasMarketplaceModifiedValidator().is_valid(modified_content_items) == []


@pytest.mark.parametrize(
    "modified_pack, old_pack",
    [
        (ALL_MARKETPLACES, ALL_MARKETPLACES),
        (ALL_MARKETPLACES, XSIAM_MARKETPLACE),
        (XSIAM_MARKETPLACE, XSIAM_MARKETPLACE),
    ],
)
def test_WasMarketplaceModifiedValidator__a_pack_is_modified__passes(
    modified_pack, old_pack
):
    """
    Given:
        - Modified `Pack` and Old `Pack` iterables.
        - Case 1: Modified `Pack` and Old `Pack` have all marketplaces.
        - Case 2: Modified `Pack` has all marketplaces and Old `Pack` has only `XSIAM`.
        - Case 3: Modified `Pack` and Old `Pack` have only `XSIAM`.

    When:
        - Calling the `WasMarketplaceModifiedValidator` function.

    Then:
        - The results should be as expected.
        - Case 1: Should pass the validation since the user didn't change anything or removed all marketplaces which is equal to adding all marketplaces.
        - Case 2: Should pass the validation since the user added marketplaces or removed all marketplaces which is equal to adding all marketplaces.
        - Case 3: Should pass the validation since the user didn't change anything or removed all marketplaces which is equal to adding all marketplaces.
    """
    modified_content_item = [create_pack_object()]
    old_content_item = [create_pack_object()]
    modified_content_item[0].marketplaces = modified_pack
    old_content_item[0].marketplaces = old_pack

    create_old_file_pointers(modified_content_item, old_content_item)
    assert WasMarketplaceModifiedValidator().is_valid(modified_content_item) == []


@pytest.mark.parametrize(
    "modified_pack, old_pack",
    [(XSIAM_MARKETPLACE, ALL_MARKETPLACES), (XSIAM_MARKETPLACE, XSOAR_MARKETPLACE)],
)
def test_WasMarketplaceModifiedValidator__a_pack_is_modified__fails(
    modified_pack, old_pack
):
    """
    Given:
        - Modified `Pack` and Old `Pack` iterables.
        - Case 1: Modified `Pack` has only `XSIAM` and Old `Pack` has all marketplaces.
        - Case 2: Modified `Pack` has only `XSIAM` and Old `Pack` has only `XSOAR`.

    When:
        - Calling the `WasMarketplaceModifiedValidator` function.

    Then:
        - The results should be as expected.
        - Case 1: Should fail the validation since the user removed marketplaces.
        - Case 2: Should fail the validation since the user replaced one marketplace with a different one.
    """
    modified_content_item = [create_pack_object()]
    old_content_item = [create_pack_object()]
    modified_content_item[0].marketplaces = modified_pack
    old_content_item[0].marketplaces = old_pack

    create_old_file_pointers(modified_content_item, old_content_item)
    results = WasMarketplaceModifiedValidator().is_valid(modified_content_item)
    assert (
        results[0].message
        == "You can't delete current marketplaces or add new ones if doing so will remove existing ones. Please undo the change or request a forced merge."
    )


def test_WasMarketplaceModifiedValidator__renamed__fails():
    """
    Given:
        - Renamed `Integration` and `Script` iterables, each moved into a new pack.
        - Old host-pack hade only `XSOAR` in pack level.
        - renamed host-pack has all marketplaces in pack level.

    When:
        - Calling the `WasMarketplaceModifiedValidator` function.

    Then:
        - The results should be as expected.
        - Should fail the validation since moving to a different pack with less marketplaces is not allowed.

    """
    renamed_content_items = [
        create_integration_object(pack_info={"marketplaces": XSOAR_MARKETPLACE}),
        create_script_object(pack_info={"marketplaces": XSOAR_MARKETPLACE}),
    ]
    renamed_content_items[0].git_status = renamed_content_items[
        1
    ].git_status = GitStatuses.RENAMED
    old_content_items = [create_integration_object(), create_script_object()]

    old_content_items[0].marketplaces = old_content_items[
        1
    ].marketplaces = ALL_MARKETPLACES_FOR_IN_PACK
    create_old_file_pointers(renamed_content_items, old_content_items)

    with ChangeCWD(REPO.path):
        results = WasMarketplaceModifiedValidator().is_valid(renamed_content_items)
        assert (
            results[0].message
            == "You can't delete current marketplaces or add new ones if doing so will remove existing ones. Please undo the change or request a forced merge."
        )
        assert len(results) == 2


def test_WasMarketplaceModifiedValidator__renamed__passes():
    """
    Given:
        - Renamed `Integration` and `Script` iterables, each moved into a new pack.
        - Renamed host-pack hade only `XSOAR` in pack level.
        - old host-pack has all marketplaces in pack level.

    When:
        - Calling the `WasMarketplaceModifiedValidator` function.

    Then:
        - The results should be as expected.
        - Should pass the validation since the new host has all marketplaces in pack level.

    """
    renamed_content_items = [
        create_integration_object(
            pack_info={"marketplaces": ALL_MARKETPLACES_FOR_IN_PACK}
        ),
        create_script_object(pack_info={"marketplaces": ALL_MARKETPLACES_FOR_IN_PACK}),
    ]
    renamed_content_items[0].git_status = renamed_content_items[
        1
    ].git_status = GitStatuses.RENAMED
    old_content_items = [create_integration_object(), create_script_object()]

    old_content_items[0].marketplaces = old_content_items[
        1
    ].marketplaces = XSOAR_MARKETPLACE
    create_old_file_pointers(renamed_content_items, old_content_items)

    with ChangeCWD(REPO.path):
        assert WasMarketplaceModifiedValidator().is_valid(renamed_content_items) == []


@pytest.mark.parametrize(
    "content_items, old_content_items, expected_number_of_failures, expected_msgs",
    [
        (
            [
                create_script_object(paths=["outputs"], values=[[]]),
                create_script_object(
                    paths=["outputs"],
                    values=[[{"contextPath": "output_1", "description": "test_1"}]],
                ),
                create_script_object(
                    paths=["outputs"],
                    values=[[{"contextPath": "output_2", "description": "test_2"}]],
                ),
            ],
            [
                create_script_object(paths=["outputs"], values=[[]]),
                create_script_object(paths=["outputs"], values=[[]]),
                create_script_object(
                    paths=["outputs"],
                    values=[[{"contextPath": "output_2", "description": "test_2"}]],
                ),
            ],
            0,
            [],
        ),
        (
            [
                create_script_object(
                    paths=["outputs"],
                    values=[
                        [
                            {"contextPath": "output_1", "description": "test_1"},
                            {"contextPath": "output_2", "description": "test_1"},
                        ]
                    ],
                ),
                create_script_object(
                    paths=["outputs"],
                    values=[[{"contextPath": "output_5", "description": "test_2"}]],
                ),
                create_script_object(paths=["outputs"], values=[[]]),
            ],
            [
                create_script_object(
                    paths=["outputs"],
                    values=[[{"contextPath": "output_2", "description": "test_1"}]],
                ),
                create_script_object(
                    paths=["outputs"],
                    values=[[{"contextPath": "output_3", "description": "test_2"}]],
                ),
                create_script_object(
                    paths=["outputs"],
                    values=[[{"contextPath": "output_4", "description": "test_3"}]],
                ),
            ],
            2,
            [
                "The following output keys: output_3. Has been removed, please undo.",
                "The following output keys: output_4. Has been removed, please undo.",
            ],
        ),
    ],
)
def test_IsBreakingContextOutputBackwardsValidator_is_valid(
    content_items: List[Script],
    old_content_items: List[Script],
    expected_number_of_failures: int,
    expected_msgs: List[str],
):
    """
    Given
    content_items and old content items.
        - Case 1: Three valid scripts:
            - One old script without outputs and a modified script without outputs.
            - One old script without outputs and a modified script with outputs.
            - One old script with outputs and a modified script with the same outputs.
        - Case 2: Two invalid scripts:
            - One old script with 1 output and a modified script with the same output and a new one.
            - One old script with 1 output and a modified script with a different output.
            - One old script with 1 output and a modified script without outputs.
    When
    - Calling the IsBreakingContextOutputBackwardsValidator is valid function.
    Then
        - Make sure the validation fail when it needs to and the right error message is returned.
        - Case 1: Shouldn't fail any.
        - Case 2: Should fail only the last two.
    """
    create_old_file_pointers(content_items, old_content_items)
    results = IsBreakingContextOutputBackwardsValidator().is_valid(content_items)
    assert len(results) == expected_number_of_failures
    assert all(
        [
            result.message == expected_msg
            for result, expected_msg in zip(results, expected_msgs)
        ]
    )


@pytest.mark.parametrize(
    "content_items, old_content_items",
    [
        pytest.param(
            [
                create_integration_object(paths=["fromversion"], values=["5.0.0"]),
                create_integration_object(paths=["fromversion"], values=["5.0.0"]),
            ],
            [
                create_integration_object(paths=["fromversion"], values=["6.0.0"]),
                create_integration_object(paths=["fromversion"], values=["5.0.0"]),
            ],
            id="Case 1: integration - fromversion changed",
        ),
        pytest.param(
            [
                create_script_object(paths=["fromversion"], values=["5.0.0"]),
                create_script_object(paths=["fromversion"], values=["5.0.0"]),
            ],
            [
                create_script_object(paths=["fromversion"], values=["6.0.0"]),
                create_script_object(paths=["fromversion"], values=["5.0.0"]),
            ],
            id="Case 2: script - fromversion changed",
        ),
        pytest.param(
            [
                create_incident_type_object(paths=["fromVersion"], values=["5.0.0"]),
                create_incident_type_object(paths=["fromVersion"], values=["6.0.0"]),
            ],
            [
                create_incident_type_object(paths=["fromVersion"], values=["5.0.0"]),
                create_incident_type_object(paths=["fromVersion"], values=["5.0.0"]),
            ],
            id="Case 3: incident type - fromversion changed",
        ),
        pytest.param(
            [
                create_incoming_mapper_object(paths=["fromVersion"], values=["5.0.0"]),
                create_incoming_mapper_object(paths=["fromVersion"], values=["6.0.0"]),
            ],
            [
                create_incoming_mapper_object(paths=["fromVersion"], values=["5.0.0"]),
                create_incoming_mapper_object(paths=["fromVersion"], values=["5.0.0"]),
            ],
            id="Case 4: mapper - fromversion changed",
        ),
    ],
)
def test_IsValidFromversionOnModifiedValidator_is_valid_fails(
    content_items, old_content_items
):
    """
    Given:
        - Case 1: two content item of type 'Integration', one with modified `fromversion`.
        - Case 2: two content item of type 'Script', one with modified `fromversion`.
        - Case 3: two content item of type 'Incident Type', one with modified `fromversion`.
        - Case 4: two content item of type 'Mapper', one with modified `fromversion`.
    When:
        - Calling the `IsValidFromversionOnModifiedValidator` validator.
    Then:
        - The is_valid function will catch the change in `fromversion` and will fail the validation only on the relevant content_item.
    """
    create_old_file_pointers(content_items, old_content_items)
    result = IsValidFromversionOnModifiedValidator().is_valid(content_items)

    assert (
        len(result) == 1
        and result[0].message
        == "Changing the minimal supported version field `fromversion` is not allowed. Please undo, or request a force merge."
    )


def create_dummy_integration_with_context_path(
    command_name: str, context_path: str
) -> Integration:

    integration = create_integration_object()
    command = Command(name=command_name)
    command.outputs = [Output(contextPath=context_path)]
    integration.commands = [command]

    return integration


def test_IsContextPathChangedValidator():
    """
    Given
    integration and old integration.
        - Case 1: no changes in context path - a valid integration
        - Case 2: context path has been changed - an invalid integration
    When
    - Calling the IsContextPathChangedValidator.
    Then
        - Make sure the validation fail when it needs to and the right error message is returned.
        - Case 1: Shouldn't fail any.
        - Case 2: Should fail.
    """
    command_name = "command"
    old_context_path = "something.else"

    new_integration = create_dummy_integration_with_context_path(
        command_name=command_name, context_path=old_context_path
    )
    old_integration = create_dummy_integration_with_context_path(
        command_name=command_name, context_path=old_context_path
    )

    new_integration.old_base_content_object = old_integration

    # integration is valid so we get an empty list
    assert not IsContextPathChangedValidator().is_valid(content_items=[new_integration])

    new_integration.commands[0].outputs[0].contextPath = f"{old_context_path}1"

    # integration is invalid, so we get a list which contains ValidationResult
    errors = IsContextPathChangedValidator().is_valid(content_items=[new_integration])
    assert errors, "Should have failed validation"
    assert old_context_path in errors[0].message
    assert errors[0].message.startswith(
        "Changing output context paths is not allowed. Restore the following outputs:"
    )


def test_IsContextPathChangedValidator_remove_command():
    """
    Given
    -  an integration and its previous version:
        in the new integration, a command has been removed
    When
    - Calling the IsContextPathChangedValidator.
    Then
     - Make sure the validation fail and the right error message is returned.
    """
    command_name = "command"
    old_context_path = "something.else"

    new_integration = create_integration_object()
    old_integration = create_dummy_integration_with_context_path(
        command_name=command_name, context_path=old_context_path
    )

    new_integration.old_base_content_object = old_integration

    # integration is invalid, since command was removed
    errors = IsContextPathChangedValidator().is_valid(content_items=[new_integration])

    assert errors, "Should have failed validation"
    assert (
        f"Command {command_name} has been removed from the integration. This is a breaking change, and is not allowed."
        in errors[0].message
    )


@pytest.mark.parametrize(
    "content_items, old_content_items",
    [
        pytest.param(
            [
                create_integration_object(paths=["toversion"], values=["6.0.0"]),
                create_integration_object(paths=["toversion"], values=["5.0.0"]),
            ],
            [
                create_integration_object(paths=["toversion"], values=["5.0.0"]),
                create_integration_object(paths=["toversion"], values=["5.0.0"]),
            ],
            id="Case 1: integration - toversion changed",
        ),
        pytest.param(
            [
                create_script_object(paths=["toversion"], values=["6.0.0"]),
                create_script_object(paths=["toversion"], values=["5.0.0"]),
            ],
            [
                create_script_object(paths=["toversion"], values=["5.0.0"]),
                create_script_object(paths=["toversion"], values=["5.0.0"]),
            ],
            id="Case 2: script - toversion changed",
        ),
    ],
)
def test_IsValidToversionOnModifiedValidator_is_valid(content_items, old_content_items):
    """
    Given:
        - Case 1: two content item of type 'Integration', one with modified `toversion`.
        - Case 2: two content item of type 'Script', one with modified `toversion`.
    When:
        - Calling the `IsValidToversionOnModifiedValidator` validator.
    Then:
        - The is_valid function will catch the change in `toversion` and will fail the validation only on the relevant content_item.
    """
    create_old_file_pointers(content_items, old_content_items)
    result = IsValidToversionOnModifiedValidator().is_valid(content_items)

    assert (
        len(result) == 1
        and result[0].message
        == "Changing the maximal supported version field `toversion` is not allowed. Please undo, or request a force merge."
    )


def test_args_name_change_validator__fails():
    """
    Given:
        - Script content item with a changed argument name.
        - Old Script content item with the old argument name.

    When:
        - Calling the `HaveTheArgsChangedValidator` function.

    Then:
        - Ensure the results are as expected with the changed argument name in the message.
    """
    modified_content_items = [
        create_script_object(paths=["args[0].name"], values=["new_arg"])
    ]
    old_content_items = [
        create_script_object(paths=["args[0].name"], values=["old_arg"])
    ]

    create_old_file_pointers(modified_content_items, old_content_items)

    results = ArgsNameChangeValidator().is_valid(modified_content_items)
    assert "old_arg." in results[0].message


def test_args_name_change_validator__passes():
    """
    Given:
        - Script content item with a new argument name, and an existing argument name.
        - Old Script content item with the existing argument name.
    When:
        - Calling the `HaveTheArgsChangedValidator` function.

    Then:
        - The results should be as expected.
        - Should pass the validation since the user didn't change existing argument names, only added new ones.
    """
    modified_content_items = [
        create_script_object(paths=["args[0].name"], values=["old_arg"])
    ]
    new_arg = create_script_object(paths=["args[0].name"], values=["new_arg"]).args[0]
    modified_content_items[0].args.append(new_arg)
    old_content_items = [
        create_script_object(paths=["args[0].name"], values=["old_arg"])
    ]

    create_old_file_pointers(modified_content_items, old_content_items)
    assert not ArgsNameChangeValidator().is_valid(modified_content_items)
