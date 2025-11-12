var agreementJson = {
  insured_name: "ABC Construction",
  holder_name: "McDonald’s Corporation",
  contract_start_date: "10/01/2025",
  contract_end_date: "10/02/2026",
  policy_types: [
    "Commercial General Liability",
    "Automobile Liability",
    "Workers’ Compensation",
    "Umbrella/Excess Liability",
  ],
  coverages: {
    "Commercial General Liability": {
      required_limit_per_occurrence: "$1,000,000",
      required_limit_aggregate: "$2,000,000",
    },
    "Automobile Liability": {
      required_limit: "$1,000,000",
    },
    "Umbrella/Excess Liability": {
      required_limit: "$2,000,000",
    },
  },
  insurance_requirements: {
    additional_insured: "McDonald’s Corporation",
    certificates_of_insurance: "Prior to commencement of work",
    waiver_of_subrogation: "In favor of McDonald’s",
  },
  additional_requirements: null,
  endorsements: null,
  waiver_of_subrogation: "In favor of McDonald’s",
  policy_numbers: null,
  other_details: {
    Scope_of_Work: "Parking lot renovation at McDonald’s location",
    Contract_Price: "$[Amount], payable in installments",
    Timeline: "Work to commence on [Start Date] and be completed by [End Date]",
    Indemnification:
      "Contractor agrees to indemnify McDonald’s from any claims",
    Compliance: "Contractor to comply with federal, state, and local laws",
    Termination: "McDonald’s may terminate Agreement with written notice",
    Dispute_Resolution:
      "Disputes to be resolved through mediation and arbitration in [Jurisdiction]",
  },
};

var accordJson = {
  insured_name: "NAMED INSUREDPOLICY",
  holder_name: null,
  policy_start_date: "POLICY EFF(MM/DD/YYYY)",
  policy_end_date: "POLICY EXP(MM/DD/YYYY)",
  policy_types: [
    "AUTOMOBILE LIABILITY",
    "WORKERS COMPENSATION AND EMPLOYERS' LIABILITY",
    "GENERAL AGGREGATE",
    "COMMERCIAL GENERAL LIABILITY",
  ],
  coverages: {
    "PROPERTY DAMAGE": "$$$",
    "BODILY INJURY (Per accident)": "$",
    "BODILY INJURY (Per person)": "$",
    "COMBINED SINGLE LIMIT": "$",
  },
  insurance_company: "CARRIER",
  policy_numbers: "POLICY NUMBER",
  endorsements: null,
  waiver_of_subrogation: "SUBRWVD",
  other: {
    "DESCRIPTION OF OPERATIONS / LOCATIONS / VEHICLES":
      "ACORD 101, Additional Remarks Schedule, may be attached if more space is required",
    "ADDITIONAL REMARKS": {
      "FORM TITLE": null,
      "FORM NUMBER": null,
      "ADDITIONAL REMARKS FORM": "SCHEDULE TO ACORD FORM",
    },
  },
};
