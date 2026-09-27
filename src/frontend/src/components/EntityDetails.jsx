import {
  User,
  Phone,
  Smartphone,
  CreditCard,
  Cpu,
  ArrowRightLeft,
  MapPin,
} from "lucide-react";

const icons = {
  PERSON: User,
  PHONE: Phone,
  SIM: Smartphone,
  DEVICE: Cpu,
  BANK_ACCOUNT: CreditCard,
  TRANSACTION: ArrowRightLeft,
  LOCATION: MapPin,
};

function EntityDetails({
  entity,
}) {
  if (!entity) {
    return (
      <div className="entity-details empty">

        <div className="empty-icon">
          ⌁
        </div>

        <h3>
          Select an entity
        </h3>

        <p>
          Click any person, device,
          phone, account or transaction
          in the network to inspect
          its details.
        </p>

      </div>
    );
  }

  const Icon =
    icons[entity.type] ||
    User;

  return (
    <div className="entity-details">

      <div className="entity-header">

        <div className="entity-icon">

          <Icon size={21} />

        </div>

        <div>

          <span>
            {entity.type}
          </span>

          <h3>
            {entity.name}
          </h3>

        </div>

      </div>

      <div className="entity-role">
        {entity.role}
      </div>

      <div className="detail-section">

        <h4>
          DESCRIPTION
        </h4>

        <p>
          {entity.description ||
            "No description available."}
        </p>

      </div>

      <div className="detail-section">

        <h4>
          ENTITY ID
        </h4>

        <code>
          {entity.id}
        </code>

      </div>

      <div className="detail-section">

        <h4>
          INVESTIGATION STATUS
        </h4>

        <div className="status-warning">
          Investigation Relevant
        </div>

      </div>

    </div>
  );
}

export default EntityDetails;